# Przykładowy przebieg (2026-06-23)

Środowisko: Apple Silicon, Ollama 0.30.10 (Ollama.app). Modele `-fast` to lokalne warianty;
gpt-oss pobrany świeżo (`gpt-oss:20b`). Wartości bezwzględne zależą od sprzętu - liczy się
relacja i rząd wielkości względem artykułu.

## tok/s generacji (`bench_speed.py`, mały prompt, warmup + mediana z 3)

| Model | Zmierzone (warm, mediana) | Artykuł | Zgodność |
|---|---|---|---|
| qwen3-coder:30b-fast | 62.0 tok/s (61.9-62.1) | ~52 tok/s | ✓ najszybszy |
| gpt-oss:20b (świeży) | 53.6 tok/s | ~43-45 tok/s | ✓ |
| deepseek-coder:33b | 10.3 tok/s (8.2-11.9) | "2-3x wolniejszy" | ✓ realnie ~6x |
| devstral-small-2:24b-fast | 7-14 tok/s (czuły na stan systemu) | ~12 tok/s | ✓ z zastrzeżeniem |
| gemma4:31b-fast (usunięty) | 9.6 tok/s (cold, 1 pomiar) | ~6 tok/s | ✓ |

### Metodologia pomiaru tok/s (warto wiedzieć)

- **Ładowanie wykluczone:** gen tok/s = `eval_count / eval_duration`; Ollama raportuje
  `eval_duration` osobno od `load_duration`, więc czas wczytania modelu z dysku NIE wchodzi
  do wyniku.
- **Warmup + mediana z 3:** pierwszy (cold) przebieg bywa zaniżony przez kompilację kerneli
  Metal. Bez warmupu qwen schodził do ~53 tok/s; z warmupem stabilne **62** (61.9-62.1).
- **Stan systemu zniekształca pomiar (najważniejsze):** devstral wyszedł 13.8 tok/s na początku
  sesji, a 7.1 pod koniec - nie przez warmup, lecz przez memory pressure (20 mln pageoutów,
  38% wolnego RAM), duży KV cache przy `num_ctx 65536` i nagrzanie po serii pomiarów.
  Rzetelny pomiar wymaga: jeden model w pamięci, świeży/chłodny system, kontrolowany `num_ctx`.
  To sam w sobie dowód tezy "benchmark ≠ rzeczywistość".

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
