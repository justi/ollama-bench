# Konfiguracja modeli - default vs best (Ollama)

Dla każdego modelu: parametry DOMYŚLNE (z `ollama show --parameters`) i NAJLEPSZE (z pomiarów
tego benchmarku + ustaleń z small-models-local-setup). Gotowe pliki `Modelfile` w `configs/`.

## Jak zastosować best config

```bash
# 1. Pobierz model bazowy (jeśli nie masz)
ollama pull qwen3-coder:30b

# 2. Zbuduj wariant best z gotowego Modelfile
ollama create qwen-coder-best -f configs/qwen-coder.best.Modelfile

# 3. Używaj
ollama run qwen-coder-best "..."
```

## STEROWANIE THINKING (kluczowe!)

Modelfile ustawia sampling, ale NIE thinking. Thinking kontrolujesz osobno:

| Sytuacja | Jak |
|---|---|
| Do KODU u modeli thinking (qwen3.6, r1, north) | `ollama run MODEL --think=false "..."` lub API `{"think": false}` |
| Do REASONINGU u modeli thinking | zostaw domyślnie (thinking ON) |
| gpt-oss (thinking HARDCODED) | NIE da się wyłączyć; minimalizacja: `--think=low` (nie false!) |

**Reguła:** thinking pomaga reasoningowi, ale u Qwen-distill (qwen3.6, deepseek-r1) PSUJE kod
(ginie w myśleniu). Do kodu wyłączaj, do logiki zostaw.

## num_ctx 8192 - profil benchmarkowy (uwaga przy agentach)

Wszystkie configi używają `num_ctx 8192`: bezpieczne dla 64 GB RAM (domyślne 128K/256K = ogromny
KV cache, deepseek-r1 = 54 GB = CRASH) i wystarczające dla zadań benchmarku (prompty kodowe
~500-800 tok, zagadki krótkie). ALE do pracy agentowej / full-repo / long-context 8192 jest za
małe - tam zrób osobny wariant (16k-32k) po sprawdzeniu zapasu RAM. To świadomy trade-off:
benchmark mierzy jakość per-zadanie, nie pojemność kontekstu.

## num_predict 3000 - ochrona przed ucięciem (modele thinking)

Modele thinking (gpt-oss, north, qwen3.6, deepseek-r1) mają w configach `num_predict 3000`:
thinking zjada budżet tokenów, a przy zbyt małym limicie cała odpowiedź ginie w myśleniu (gpt-oss
przy 1500 = 0 słów widocznej odpowiedzi, zmierzone). Dla `--think=false` (kod) nieszkodliwe.

---

## qwen3-coder:30b - dedykowany koder (MoE 30B/3B), bez thinking

| | default | best |
|---|---|---|
| temperature | 0.7 | 0.7 |
| top_k | 20 | 20 |
| top_p | 0.8 | 0.8 |
| repeat_penalty | 1.05 | 1.05 |
| num_ctx | (auto, duży) | **8192** (oszczędność RAM) |

Best ≈ default - qwen-coder jest dobrze skonfigurowany fabrycznie. Jedyna zmiana to num_ctx
(na 64 GB Ollama daje 256K = duży KV cache; 8192 wystarcza i zwalnia RAM). Bez thinking.
Najszybszy output (~62 tok/s), kod 5/9 expert (2. miejsce).

## gpt-oss:20b - thinking HARDCODED (harmony), reasoning_effort

| | default | best (kod) | best (reasoning) |
|---|---|---|---|
| temperature | 1.0 | **0.3** | 1.0 |
| num_predict | (auto) | **3000** | 3000 |
| num_ctx | (auto) | 8192 | 8192 |
| thinking | medium (default) | `--think=low` | `--think=high` |

temp=0 daje 100% pętli (zmierzone) - NIGDY nie ustawiaj 0. num_predict 3000 chroni przed
ucięciem odpowiedzi (thinking zjada budżet). Thinking nie wyłączysz - poziom sterujesz tylko
przez `--think=low|medium|high` (CLI/API), NIE przez `PARAMETER reasoning_effort` w Modelfile.
Domyślny poziom to `medium`. `configs/gpt-oss.best.Modelfile` to profil KODOWY (temp 0.3); do
reasoningu użyj temp 1.0 + `--think=high`. Reasoning 5.0 (stabilny), kod 4/9.

## devstral-small-2:24b-fast - Mistral, bez thinking

| | default (fast) | best |
|---|---|---|
| temperature | 0.15 | 0.2 |
| top_p | (auto) | 0.9 |
| num_ctx | 65536 | **8192** |

Bazą jest faktycznie benchmarkowany tag `devstral-small-2:24b-fast` (default num_ctx 65536, temp
0.15), NIE publiczny `devstral:24b` (inny artefakt, 128K kontekstu). Niska temperatura sprzyja
determinizmowi. num_ctx 8192 zamiast 65536 (oszczędność ~17 GB RAM). Wolny output (~12 tok/s),
ale najlepszy reasoning (5.33). Bez thinking.

## north-mini-code-1.0 - Cohere MoE coder (30B/3B), THINKING

| | default | best (kod) | best (reasoning) |
|---|---|---|---|
| temperature | 1.0 | **0.7** | 0.7 |
| top_p | 0.95 | 0.8 | 0.95 |
| num_ctx | (auto) | 8192 | 8192 |
| num_predict | (auto) | 3000 | 3000 |
| thinking | ON | **`--think=false`** | ON |

UWAGA: north to thinking-model. `configs/north.best.Modelfile` to profil KODOWY (top_p 0.8). Do
KODU używaj `--think=false` - inaczej kod ginie w myśleniu (na trudnych zadaniach). Do reasoningu
zostaw thinking ON i nadpisz `top_p 0.95` w runtime. Najszybszy output bez thinking (~65 tok/s),
ale na nietrywialnym kodzie słaby (do weryfikacji z no-think).

## phi4:14b - Microsoft, bez thinking

| | default | best |
|---|---|---|
| temperature | (auto ~0.8) | **0.7** |
| num_ctx | (auto) | 8192 |

phi4 na natywnej (wyższej) temperaturze jest chaotyczny na reasoningu (zakres 4); temp 0.7 daje
stabilność (zakres 0, reasoning 5.0). Mały (9 GB), dobra jakość. Bez thinking.

## qwen3.6:35b-a3b - Qwen3.6 35B-A3B (ogólny), THINKING

| | default | best (params unsloth) |
|---|---|---|
| temperature | 1.0 | **0.7** |
| top_p | 0.95 | **0.8** |
| top_k | 20 | 20 |
| min_p | 0 | 0 |
| presence_penalty | 1.5 | 1.5 |
| repeat_penalty | 1.0 | 1.0 |
| num_ctx | (auto) | 8192 |
| num_predict | (auto) | 3000 |
| thinking | ON | **`--think=false` do kodu** |

Parametry z rekomendacji unsloth (kluczowa różnica: top_p 0.8 nie 0.95). Z no-think jest
NAJLEPSZYM koderem trudnych zadań (6/9 expert!). Z thinking ON kod ginie (4/8). Do reasoningu
zostaw thinking.

## deepseek-r1:32b - DeepSeek-R1-Distill-Qwen (reasoning), THINKING

| | default | best |
|---|---|---|
| temperature | (auto) | 0.6 |
| num_ctx | **131072 (= 54 GB RAM, CRASH na 64 GB!)** | **8192** |
| num_predict | (auto) | 3000 |
| thinking | ON | `--think=false` do kodu |

KRYTYCZNE: domyślny num_ctx 128K zajmuje 54 GB i wywala model na 64 GB. ZAWSZE ustaw num_ctx
8192. Bardzo wolny (~4 tok/s) - reasoning-first model. Do kodu `--think=false` (kod 4/9 z no-think).
