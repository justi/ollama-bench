# Przykładowy przebieg (2026-06-23)

Środowisko: Apple Silicon, Ollama 0.30.10 (Ollama.app). Modele `-fast` to lokalne warianty;
gpt-oss pobrany świeżo (`gpt-oss:20b`). Wartości bezwzględne zależą od sprzętu - liczy się
relacja i rząd wielkości względem artykułu.

## tok/s generacji (izolacja: 1 model w pamięci, warmup + mediana z 3)

Dwa SPÓJNE zestawy - nie mieszamy fast z default (to byłoby porównanie różnych rzeczy).

### Zestaw DEFAULT (publiczne tagi - reprodukowalne dla czytelnika)

| Model | tok/s (mediana) | przebiegi |
|---|---|---|
| qwen3-coder:30b | **54.8** | 55.7 / 54.8 / 53.8 |
| gpt-oss:20b | **48.1** | 47.0 / 48.1 / 48.5 |
| deepseek-coder:33b | **10.4** | 10.5 / 10.3 / 10.4 |
| devstral:24b | **8.9** | 9.3 / 8.9 / 7.7 |

### Zestaw FAST (zoptymalizowane warianty - mniejszy num_ctx, dostrojony sampling)

| Model | tok/s (mediana) | vs default |
|---|---|---|
| qwen3-coder:30b-fast | **61.7** | +13% |
| gpt-oss-fast | **52.6** | +9% |
| deepseek-fast | **14.2** | **+37%** |
| devstral-small-2:24b-fast | **11.8** | **+33%** |

Wnioski:
- **Ranking spójny w obu zestawach:** qwen > gpt-oss ≫ deepseek > devstral.
- **Fast realnie przyspiesza o +9% do +37%.** Największy zysk tam, gdzie default ma duży
  kontekst (deepseek, devstral 128K) - fast tnie `num_ctx` do 8192, mniejszy KV cache =
  szybsza generacja. qwen/gpt-oss już dobrze zoptymalizowane, więc mniejszy zysk.
- Deepseek (10.4 / 14.2) jest ~5x wolniejszy od qwen - teza artykułu "2-3x wolniejszy"
  (mierzona jako całkowity czas zadania) jest raczej zaniżona w czystej prędkości generacji.

### Metodologia pomiaru tok/s (dlaczego tym liczbom można ufać)

- **Ładowanie wykluczone:** gen tok/s = `eval_count / eval_duration`; Ollama raportuje
  `eval_duration` osobno od `load_duration`, więc czas wczytania modelu z dysku NIE wchodzi.
- **Warmup + mediana z 3:** cold start zaniżał qwen (~53 bez warmupu vs ~62 z); mediana
  ignoruje pojedyncze outliery (np. devstral miał w jednym przebiegu spadek do 5.3 -
  mediana 11.8 go pominęła).
- **Izolacja (1 model w pamięci):** to było kluczowe. Bez izolacji deepseek wychodził 10.3,
  devstral 7.1 - zaniżone przez konkurencję o VRAM/RAM (memory pressure, pageouty). Po
  wymuszeniu jednego modelu w pamięci: deepseek 14.2, devstral 11.8. Więcej niż jeden model
  w pamięci = niewiarygodny benchmark. To zarazem dowód tezy "benchmark ≠ rzeczywistość".

## num_predict i thinking overflow (`bench_numpredict.py`, gpt-oss:20b)

| num_predict | słowa odpowiedzi | czas | artykuł |
|---|---|---|---|
| 1500 | **0** (sam thinking, pusty output) | 64 s | ~293 słów |
| 3000 | **512** | 93 s | ~747 słów |

Najmocniejsze potwierdzenie: przy limicie 1500 gpt-oss zużył wszystkie tokeny na "myślenie"
i nie zwrócił ani słowa odpowiedzi - dokładnie "thinking overflow" z artykułu. Podniesienie
do 3000 odblokowało pełną odpowiedź. Mechanizm i relacja odtworzone (wartości bezwzględne inne).

## Zagadki logiczne = jakość reasoning (`bench_reasoning.py`, zestaw fast, ocena ręczna)

| Model | Score (human) | auto | Uwaga |
|---|---|---|---|
| gpt-oss-fast | **6/6** | 6/6 | wszystkie poprawne, w tym paradoks rycerz/łotr |
| devstral-small-2:24b-fast | **6/6** | 6/6 | najlepszy, pełne wywody (Z1 rozwiązany układem równań) |
| qwen3-coder:30b-fast | 4/6 | 4/6 | pomylił paradoks (Z2) i ASCII 76 (dał "V") |
| deepseek-fast | 2-3/6 | 3/6 | model KODOWY: na Z3 odmówił ("nie związane z programowaniem"), Z1 halucynacja |

Tezy z artykułu odtworzone/rozszerzone:
1. gpt-oss "2/6" w źródle wynikało z thinking overflow - z num_predict=3000 daje **6/6**.
2. devstral najlepszy na reasoning (6/6) - zgodnie ze źródłem (3/3 w oryginale).
3. deepseek-coder słaby na reasoning - to model kodowy, odmawia/halucynuje na zagadkach
   (jakość zależy od TYPU zadania - do kodu może być OK, do logiki nie).
4. automatyczna metryka rozjeżdża się z ręczną: deepseek auto 3/6, human ~2/6 (Z4 był
   wewnętrznie sprzeczny, auto zaliczył po kluczu) - teza "potrzeba human eval".

## Duży prompt (`bench_speed.py --big`, qwen vs devstral)

Pierwszy przebieg (repeat=500, ~40k tokenów - za dużo): qwen **388 s** (ukończył),
devstral **timeout >900 s**. Wartości zawyżone złą kalibracją promptu (poprawione na
repeat=160 -> ~12k tokenów), ale **relacja się potwierdza**: devstral dramatycznie wolniejszy
od qwen na dużym kontekście (nie domknął, gdy qwen tak) - teza "sliding window attention
nie skaluje się na dużym prompcie".

## MACIERZ DECYZYJNA: szybkość × jakość × energia (zestaw fast)

Trzy osie naraz - bo "najszybszy" != "najlepszy do wszystkiego":

| Model | szybkość (tok/s) | jakość reasoning (/6) | energia (kWh/1M) |
|---|---|---|---|
| gpt-oss-fast | 52.6 (2.) | **6/6** (1.) | 0.24 (2.) |
| qwen-fast | **61.7** (1.) | 4/6 (3.) | **0.20** (1.) |
| devstral-fast | 11.8 (4.) | **6/6** (1.) | 1.06 (4.) |
| deepseek-fast | 14.2 (3.) | 2-3/6 (4.) | 0.88 (3.) |

(energia kWh/1M przy ~45 W; pomnóż przez swoją cenę kWh dla kosztu w zł)

- **gpt-oss-fast - najlepszy kompromis:** 2. szybkość, najlepsza jakość (6/6), 2. energia. Domyślny wybór.
- **qwen-fast - najszybszy i najoszczędniejszy,** ale średnia jakość reasoning. Idealny do dużego
  wolumenu prostych zadań / generacji kodu.
- **devstral-fast - jakość 6/6, ale najwolniejszy i najbardziej prądożerny** (~5× energii qwena).
  Tylko gdy jakość krytyczna, a wolumen mały.
- **deepseek-fast - najsłabszy ogólnie** (wolny, prądożerny, najgorszy reasoning). ALE to model
  KODOWY - na zadaniach programistycznych może wypaść inaczej; tego wymiaru tu NIE mierzymy.

Zastrzeżenie: "jakość" = reasoning logiczny (jeden wymiar). Brakuje wymiaru stricte kodowego
(generacja kodu, znajdowanie bugów) - patrz README, sekcja o planowanym `bench_coding.py`.
