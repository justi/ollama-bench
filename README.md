# ollama-bench

Reprodukowalny benchmark lokalnych modeli LLM na Ollamie. Pozwala **samodzielnie odtworzyć liczby** podawane w artykułach o lokalnych LLM (tok/s, wpływ `num_predict`, score na zagadkach logicznych) na własnym sprzęcie.

Zero zależności poza biblioteką standardową Pythona 3 - rozmawia z Ollamą po HTTP (`/api/generate`).

## Wymagania

- Python 3.9+
- Działający serwer Ollama na `http://localhost:11434`
- Pobrane modele, które chcesz testować

```bash
# modele bazowe z artykułu (publiczne tagi)
ollama pull qwen3-coder:30b
ollama pull gpt-oss:20b
```

Adres serwera można zmienić zmienną `OLLAMA_HOST` (domyślnie `http://localhost:11434`).

## Co mierzy i którą liczbę z artykułu odtwarza

| Skrypt | Liczba z artykułu | Co robi |
|---|---|---|
| `bench_speed.py` | "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s" | tok/s generacji (`eval_count`/`eval_duration`) |
| `bench_speed.py --big` | "devstral ~40 s vs qwen ~17 s na dużym prompcie" | czas na prompcie ~12 tys. tokenów (prompt eval + gen) |
| `bench_numpredict.py` | "domyślny limit ~293 słów -> 3000 ~747 słów, ~45 s -> ~85 s" | dwa przebiegi gpt-oss z różnym `num_predict` |
| `bench_reasoning.py` | "gpt-oss 2/6, qwen 6/6 na zagadkach" | jakość reasoningu: 6 zagadek logicznych, auto-grade |
| `bench_coding.py` | jakość kodowa modeli kodowych | generacja funkcji (auto-test przez uruchomienie) + bug finding |
| `bench_cost.py` | koszt energii lokalnego inferencji | energia kWh/1M (z tok/s i poboru mocy); zł opcjonalnie |

## Uruchomienie

```bash
# wszystko naraz (zapisuje results.json)
bash run.sh

# albo pojedynczo, ze swoją listą modeli
python3 bench_speed.py qwen3-coder:30b gpt-oss:20b
python3 bench_speed.py --big qwen3-coder:30b devstral:24b
python3 bench_numpredict.py gpt-oss:20b
python3 bench_reasoning.py qwen3-coder:30b gpt-oss:20b
python3 bench_coding.py qwen3-coder:30b deepseek-coder:33b   # jakość kodowa (uruchamia wygenerowany kod!)
python3 bench_cost.py "qwen3-coder:30b=54.8" "deepseek-coder:33b=10.4"   # energia kWh/1M
```

`bench_coding.py` wykonuje (exec) kod wygenerowany przez model na lokalnych testach -
uruchamiaj tylko na zaufanych modelach lokalnych.

## Najlepsze configi per model (`configs/`)

Aktualne, rzetelne wyniki (sekcje z 2026-06) opierają się na wariantach `*-best`, zbudowanych
z `configs/*.best.Modelfile` (8 modeli: qwen-coder, gpt-oss, devstral, north, phi4, qwen36,
deepseek-r1, unsloth-q4xl). Każdy ma najlepsze parametry + `num_ctx 8192` + `num_predict 3000`.
Pełne zestawienie default vs best: `MODELS_CONFIG.md`.

```bash
ollama create qwen36-best -f configs/qwen36.best.Modelfile
python3 bench_coding.py --expert --num-predict=3000 qwen36-best            # kod, thinking ON
python3 bench_coding.py --expert --no-think --num-predict=3000 qwen36-best  # kod, thinking OFF
python3 bench_reasoning.py --runs 3 qwen36-best                            # reasoning, n=3
```

Sterowanie thinkingiem per zadanie: `--no-think` (Qwen-distill, do kodu), `--think=low|high`
(gpt-oss - nie da się wyłączyć). Wykrywanie ucięcia: flaga `TR!` gdy `done_reason=length`.

## Struktura repo

- `bench_*.py`, `_common.py` - skrypty pomiarowe
- `prompts.json` - wszystkie zadania testowe (generate_expert, generate_hard, bugfind, reasoning)
- `configs/` - 8 best Modelfile (kanoniczne, aktualne)
- `RESULTS.md`, `MODELS_CONFIG.md` - wyniki + parametry
- `articles/` - artykuły blogowe oparte na tych wynikach
- `legacy/` - stare Modelfile z wczesnych eksperymentów ("fast", usunięte modele); zachowane dla
  prowenancji starszych sekcji `RESULTS.md`, NIE używane w aktualnych pomiarach

Logi runów (`log_*.txt`) i surowe wyniki (`results_*.json`) są gitignorowane - regenerowalne.

## Disclaimer

Liczby są **zależne od sprzętu, wersji Ollamy i kwantyzacji modelu**. Wartości w artykule zmierzono na Apple M1 Max 64 GB. Twoje będą inne co do wartości bezwzględnej - chodzi o odtworzenie *rzędów wielkości i relacji* (qwen wielokrotnie szybszy od gemmy; `num_predict` realnie wydłuża odpowiedź).
