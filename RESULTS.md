# Przykładowy przebieg (2026-06-23)

Środowisko: Apple Silicon, Ollama 0.30.10 (Ollama.app). Modele `-fast` to lokalne warianty;
gpt-oss pobrany świeżo (`gpt-oss:20b`). Wartości bezwzględne zależą od sprzętu - liczy się
relacja i rząd wielkości względem artykułu.

## tok/s generacji (`bench_speed.py`, mały prompt)

| Model | Zmierzone | Artykuł | Zgodność |
|---|---|---|---|
| qwen3-coder:30b-fast | 53-60 tok/s | ~52 tok/s | ✓ najszybszy |
| gpt-oss:20b (świeży) | 54 tok/s | ~43-45 tok/s | ✓ |
| devstral-small-2:24b-fast | 13.8 tok/s | ~12 tok/s | ✓ |
| gemma4:31b-fast | 9.6 tok/s | ~6 tok/s | ✓ niezdatny do pracy interaktywnej |
| deepseek-coder:33b | 9.4 tok/s | "2-3x wolniejszy" | ✓ realnie ~5.7x w gen rate |

Relacja z artykułu (qwen wielokrotnie szybszy) - odtworzona.

**Teza o deepseeku doprecyzowana.** Artykuł mówi "2-3x wolniejszy" - to całkowity czas
zadania (jak mierzyło źródło). W czystej prędkości generacji deepseek (9.4 tok/s) jest
**~5.7x wolniejszy** od qwen/gpt-oss (~54 tok/s), czyli teza jest raczej zaniżona.
deepseek generuje tak wolno jak odrzucona gemma - na interaktywną pracę się nie nadaje.

## num_predict i thinking overflow (`bench_numpredict.py`, gpt-oss:20b)

| num_predict | słowa odpowiedzi | czas | artykuł |
|---|---|---|---|
| 1500 | **0** (sam thinking, pusty output) | 64 s | ~293 słów |
| 3000 | **512** | 93 s | ~747 słów |

Najmocniejsze potwierdzenie: przy limicie 1500 gpt-oss zużył wszystkie tokeny na "myślenie"
i nie zwrócił ani słowa odpowiedzi - dokładnie "thinking overflow" z artykułu. Podniesienie
do 3000 odblokowało pełną odpowiedź. Mechanizm i relacja odtworzone (wartości bezwzględne inne).

## Zagadki logiczne (`bench_reasoning.py`, num_predict=3000)

| Model | Score | Uwaga |
|---|---|---|
| qwen3-coder:30b-fast | 5/6 (auto 4/6) | pomylił ASCII 76 (dał "V"); auto-grade zaniżył Z1 przez markdown |
| gpt-oss:20b | 6/6 | z odpowiednim num_predict gpt-oss jest lepszy na reasoning |

To odtwarza trzy rzeczy z artykułu naraz:
1. gpt-oss "2/6" w źródle wynikało z thinking overflow - z num_predict=3000 daje **6/6**.
2. qwen jest dobry na reasoning (5/6), ale gpt-oss z budżetem tokenów go wyprzedza.
3. automatyczna metryka rozjeżdża się z ręczną oceną (qwen auto 4/6 vs human 5/6) - teza
   "automatyczne checky zawyżają/zaniżają, potrzeba human eval".

## Duży prompt (`bench_speed.py --big`, qwen vs devstral)

Pierwszy przebieg (repeat=500, ~40k tokenów - za dużo): qwen **388 s** (ukończył),
devstral **timeout >900 s**. Wartości zawyżone złą kalibracją promptu (poprawione na
repeat=160 -> ~12k tokenów), ale **relacja się potwierdza**: devstral dramatycznie wolniejszy
od qwen na dużym kontekście (nie domknął, gdy qwen tak) - teza "sliding window attention
nie skaluje się na dużym prompcie".
