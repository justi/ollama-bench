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
| `bench_reasoning.py` | "gpt-oss 2/6, qwen 6/6 na zagadkach" | 6 zagadek logicznych, auto-grade po kluczu |

## Uruchomienie

```bash
# wszystko naraz (zapisuje results.json)
bash run.sh

# albo pojedynczo, ze swoją listą modeli
python3 bench_speed.py qwen3-coder:30b gpt-oss:20b
python3 bench_speed.py --big qwen3-coder:30b devstral:24b
python3 bench_numpredict.py gpt-oss:20b
python3 bench_reasoning.py qwen3-coder:30b gpt-oss:20b
```

## Uwaga o wariantach "fast"

W artykule modele "fast" (np. `qwen-fast`) to lokalne Modelfile z dostrojonymi parametrami - nie publiczne tagi. Patrz `Modelfile.qwen-fast` i `Modelfile.gpt-oss-fast` w tym repo: zbuduj je raz przez `ollama create`, potem podaj nazwę wariantu skryptom. Wyniki tok/s będą zbliżone do bazowych; różnica `num_predict` widać dopiero w `bench_numpredict.py`.

## Disclaimer

Liczby są **zależne od sprzętu, wersji Ollamy i kwantyzacji modelu**. Wartości w artykule zmierzono na Apple M1 Max 64 GB. Twoje będą inne co do wartości bezwzględnej - chodzi o odtworzenie *rzędów wielkości i relacji* (qwen wielokrotnie szybszy od gemmy; `num_predict` realnie wydłuża odpowiedź).
