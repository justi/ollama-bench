# Model configuration - default vs best (Ollama)

For each model: DEFAULT parameters (from `ollama show --parameters`) and BEST (from this
benchmark's measurements + findings from small-models-local-setup). Ready-made `Modelfile` files in `configs/`.

> **Single source of truth: [`models.json`](models.json) + [`run_bench.py`](run_bench.py).**
> Per model it pins the sampling params AND the per-task invocation (think + num_predict). Run
> benchmarks through the dispatcher so flags are never hand-assembled (no forgotten `--no-think`,
> no guessed temp, no drifting num_predict): `python3 run_bench.py reasoning fleet --runs 3`,
> `python3 run_bench.py code gemma-best --expert`, `python3 run_bench.py speed fleet`. It prints
> the exact command per model. This prose is the human explanation; `models.json` is canonical.

## How to apply the best config

```bash
# 1. Pull the base model (if you don't have it)
ollama pull qwen3-coder:30b

# 2. Build the best variant from the ready-made Modelfile
ollama create qwen-coder-best -f configs/qwen-coder.best.Modelfile

# 3. Use it
ollama run qwen-coder-best "..."
```

## CONTROLLING THINKING (crucial!)

The Modelfile sets sampling, but NOT thinking. You control thinking separately:

| Situation | How |
|---|---|
| For CODE on thinking models (qwen3.6, r1, north) | `ollama run MODEL --think=false "..."` or API `{"think": false}` |
| For REASONING on thinking models | leave default (thinking ON) |
| gpt-oss (thinking HARDCODED) | can't be disabled; to minimize: `--think=low` (not false!) |

**Rule:** thinking helps reasoning, but on Qwen-distill (qwen3.6, deepseek-r1) it BREAKS code
(it gets lost in thinking). Disable it for code, leave it on for logic.

## num_ctx 8192 - benchmark profile (note for agents)

All configs use `num_ctx 8192`: safe for 64 GB RAM (the default 128K/256K = a huge
KV cache, deepseek-r1 = 54 GB = CRASH) and sufficient for the benchmark's tasks (coding prompts
~500-800 tok, short puzzles). BUT for agentic work / full-repo / long-context, 8192 is too
small - there, make a separate variant (16k-32k) after checking your RAM headroom. This is a deliberate trade-off:
the benchmark measures per-task quality, not context capacity.

## num_predict 3000 - protection against truncation (thinking models)

Thinking models (gpt-oss, north, qwen3.6, deepseek-r1) have `num_predict 3000` in their configs:
thinking eats the token budget, and with too small a limit the whole answer gets lost in thinking (gpt-oss
at 1500 = 0 words of visible answer, measured). For `--think=false` (code) it's harmless.

---

## qwen3-coder:30b - dedicated coder (MoE 30B/3B), no thinking

| | default | best |
|---|---|---|
| temperature | 0.7 | 0.7 |
| top_k | 20 | 20 |
| top_p | 0.8 | 0.8 |
| repeat_penalty | 1.05 | 1.05 |
| num_ctx | (auto, large) | **8192** (RAM savings) |

Best ≈ default - qwen-coder is well configured out of the box. The only change is num_ctx
(on 64 GB Ollama gives 256K = a large KV cache; 8192 is enough and frees up RAM). No thinking.
Fastest output (~62 tok/s), code 5/9 expert (2nd place).

## gpt-oss:20b - thinking HARDCODED (harmony), reasoning_effort

| | default | best (code) | best (reasoning) |
|---|---|---|---|
| temperature | 1.0 | **0.3** | 1.0 |
| num_predict | (auto) | **3000** | 3000 |
| num_ctx | (auto) | 8192 | 8192 |
| thinking | medium (default) | `--think=low` | `--think=high` |

temp=0 gives 100% loops (measured) - NEVER set 0. num_predict 3000 protects against
answer truncation (thinking eats the budget). You can't disable thinking - you control the level only
via `--think=low|medium|high` (CLI/API), NOT via `PARAMETER reasoning_effort` in the Modelfile.
The default level is `medium`. `configs/gpt-oss.best.Modelfile` is the CODING profile (temp 0.3); for
reasoning use temp 1.0 + `--think=high`. Reasoning 5.0 (stable), code 4/9.

## devstral-small-2:24b-fast - Mistral, no thinking

| | default (fast) | best |
|---|---|---|
| temperature | 0.15 | 0.2 |
| top_p | (auto) | 0.9 |
| num_ctx | 65536 | **8192** |

The base is actually the benchmarked tag `devstral-small-2:24b-fast` (default num_ctx 65536, temp
0.15), NOT the public `devstral:24b` (a different artifact, 128K context). Low temperature favors
determinism. num_ctx 8192 instead of 65536 (saves ~17 GB RAM). Slow output (~12 tok/s),
but the best reasoning (5.33). No thinking.

## north-mini-code-1.0 - Cohere MoE coder (30B/3B), THINKING

| | default | best (code) | best (reasoning) |
|---|---|---|---|
| temperature | 1.0 | **0.7** | 0.7 |
| top_p | 0.95 | 0.8 | 0.95 |
| num_ctx | (auto) | 8192 | 8192 |
| num_predict | (auto) | 3000 | 3000 |
| thinking | ON | **`--think=false`** | ON |

NOTE: north is a thinking model. `configs/north.best.Modelfile` is the CODING profile (top_p 0.8). For
CODE use `--think=false` - otherwise the code gets lost in thinking (on hard tasks). For reasoning
leave thinking ON and override `top_p 0.95` at runtime. Fastest output without thinking (~65 tok/s),
but weak on non-trivial code (to be verified with no-think).

## phi4:14b - Microsoft, no thinking

| | default | best |
|---|---|---|
| temperature | (auto ~0.8) | **0.7** |
| num_ctx | (auto) | 8192 |

phi4 at its native (higher) temperature is chaotic on reasoning (range 4); temp 0.7 gives
stability (range 0, reasoning 5.0). Small (9 GB), good quality. No thinking.

## gemma4:e4b - Google Gemma 4 E4B, thinking-capable (off by default)

| | default | best |
|---|---|---|
| temperature | 1.0 | **1.0** |
| top_k | 64 | 64 |
| top_p | 0.95 | 0.95 |
| num_ctx | (native 128K) | 8192 |

Gemma 4 E4B: 8B total weights, ~4.5B effective (MatFormer activates a sub-network), Q4_K_M,
128K native context. temp 1.0 / top_k 64 / top_p 0.95 are Google/Unsloth's recommended sampling
(HF: high temp is best for coding). temp 1.0 vs an earlier (wrong) 0.7 give IDENTICAL scores.

THINKING - IMPORTANT, the official "off by default" does NOT hold via the API. Measured (both M1
ollama 0.30.10 AND darwine 0.22.1): `think=None` (no flag) makes gemma THINK - it behaves like
`think=true` (a 20-token classify call returns empty/done=length; reasoning scores match ON). You
must pass `think=false` explicitly for the no-thinking mode. So the per-task control: code ->
`--think=false` (truly off), reasoning -> leave default or `--think=true` (thinking on).

Reasoning, re-measured cleanly (darwine, n=3, PL): true OFF (`think=false`) = 3.0; thinking ON
(`think=true` OR default `None`) = 5.0. So thinking adds ~+2.0 for gemma. The earlier "OFF 5.5 ->
ON 6.0 (+0.5)" was WRONG - that "OFF" was `think=None` = already thinking. Code (`--think=false`,
truly off) is unaffected: 5/9 expert, 5/5 default, 6/6 hard, 7/7 mutated. Speed on M1 Max: 48.9
tok/s (median of 3, isolated) = 0.256 kWh/1M - mid-pack (faster than qwen36, slower than gpt-oss/north).

Strong for its compute. Reasoning (with thinking, i.e. think=None/on): PL 5.5 / EN 5.8, beating phi4/devstral/qwen-coder. Code:
expert 5/9 (n=3), default 5/5, hard 6/6, mutated 7/7 (ties qwen36, beats the rest). Note on the
"small model" framing: by ACTIVE compute gemma (~4.5B effective) is comparable to or larger than
the qwen MoEs (qwen36 35b-a3b and qwen-coder 30b are ~3B active), so matching them is expected;
the real efficiency win is beating the DENSE phi4 (14B) and devstral (24B) at lower active cost.
Also serves as the neutral cross-family judge for grade_reasoning.py.

## qwen3.6:35b-a3b - Qwen3.6 35B-A3B (general), THINKING

| | default | best (unsloth params) |
|---|---|---|
| temperature | 1.0 | **0.7** |
| top_p | 0.95 | **0.8** |
| top_k | 20 | 20 |
| min_p | 0 | 0 |
| presence_penalty | 1.5 | 1.5 |
| repeat_penalty | 1.0 | 1.0 |
| num_ctx | (auto) | 8192 |
| num_predict | (auto) | 3000 |
| thinking | ON | **`--think=false` for code** |

Parameters from unsloth's recommendation (the key difference: top_p 0.8 not 0.95). With no-think it is
the BEST coder for hard tasks (6/9 expert!). With thinking ON the code gets lost (4/8). For reasoning
leave thinking on.

## deepseek-r1:32b - DeepSeek-R1-Distill-Qwen (reasoning), THINKING

| | default | best |
|---|---|---|
| temperature | (auto) | 0.6 |
| num_ctx | **131072 (= 54 GB RAM, CRASH on 64 GB!)** | **8192** |
| num_predict | (auto) | 3000 |
| thinking | ON | `--think=false` for code |

CRITICAL: the default num_ctx 128K takes 54 GB and crashes the model on 64 GB. ALWAYS set num_ctx
8192. Very slow (~4 tok/s) - a reasoning-first model. For code `--think=false` (code 4/9 with no-think).
