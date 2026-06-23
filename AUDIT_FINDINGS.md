# Findings — audyt poprawności pomiaru (ollama-bench)

Weryfikacja na żywym Ollama (0.30.10, localhost:11434). Pliki mają już część poprawek (poll w `isolate()`, `num_predict=256` w `--big`); poniżej stan **aktualny** + wpływ na wiarygodność wyników.

---

## KRYTYCZNY

### 1. `gen_tok_s` dla modeli „thinking" liczy tokeny myślenia, nie odpowiedzi
- **Plik:** `_common.py:100-106`, `bench_speed.py:47-52`
- **Problem:** U `gpt-oss-fast` przy `num_predict=50` było `eval_count=50`, `response=""`, a treść poszła w pole `thinking`. `gen_tok_s = eval_count / eval_duration` mierzy więc przepustowość kanału thinking, nie widocznego outputu. Porównanie z qwen/deepseek (bez thinking) fałszuje ranking tok/s i kaskadowo `bench_cost.py`.
- **Weryfikacja:** `gpt-oss-fast`: 100 tokenów eval, 0 znaków response, 396 znaków thinking; `qwen3-coder:30b-fast`: 100 tokenów, 272 znaki response.
- **Propozycja:** Dla modeli z `thinking` liczyć osobno (np. `len(response.split())` / czas albo osobne pola API); oznaczać w wynikach `metric=thinking_tokens`; nie mieszać w jednej tabeli z modelami bez thinking.

### 2. Auto-grade Monty Hall (Z4): klucz `zmieni` daje false-positive na odpowiedzi „nie zmieniaj"
- **Plik:** `prompts.json:31-32`, `bench_reasoning.py:20-28`
- **Problem:** Regex `zmieni` matchuje też `zmienic` w „**nie** warto **zmienic**" — odpowiedź „zostań przy bramce 1" może dostać punkt.
- **Weryfikacja:** `grade('Nie, nie warto zmienic. Prawdopodobienstwo 1/3.')` → match na `zmieni`.
- **Propozycja:** Wymagać `2/3` lub `66` **oraz** pozytywnej decyzji (`warto zmienic`, `tak.*zmie`), albo negacji explicite (`nie warto zmienic` → fail).

---

## WAŻNY

### 3. `isolate()` traktuje błąd `/api/ps` (`None`) jako sukces opróżnienia pamięci
- **Plik:** `_common.py:57-60`
- **Problem:** W pętli poll: `if cur is None or len(cur) == 0: break` — awaria API kończy oczekiwanie tak, jakby VRAM był pusty. Benchmark rusza z niezweryfikowaną izolacją.
- **Weryfikacja:** symulacja: po 2× `['model']` → `None` → pętla się kończy.
- **Propozycja:** `None` → retry/abort z błędem; sukces tylko przy `cur == []` po potwierdzonym unload.

### 4. `isolation_ok` wrażliwe na sufiks `:latest` — fałszywe alarmy izolacji
- **Plik:** `bench_speed.py:42-43`
- **Problem:** `loaded == [model]` wymaga dokładnej nazwy. Ollama w `/api/ps` zwraca `deepseek-fast:latest`, a skrypt dostaje `deepseek-fast` → `isolated=false` mimo że w pamięci jest wyłącznie ten model.
- **Weryfikacja:** `loaded=['deepseek-fast:latest']`, `model='deepseek-fast'` → `isolation_ok=False`.
- **Propozycja:** Normalizacja (`name.split(':')[0]` lub dopasowanie `name == model or name.startswith(model+':')`).

### 5. `isolate()` po timeout nie sygnalizuje niepowodzenia
- **Plik:** `_common.py:45-62`
- **Problem:** Po 30 s z modelami wciąż w `/api/ps` funkcja kończy się cicho; `bench_speed` mierzy dalej na skażonym stanie (dokumentowany wpływ: deepseek 10.3 → 14.2 tok/s po izolacji).
- **Propozycja:** Zwracać status (`isolated: bool`); przy timeout → `error` w `results_speed.json`, nie raportować tok/s.

### 6. `run_generated()` — ścisłe `!=` zaniża wynik kodowy (false-negatives)
- **Plik:** `bench_coding.py:47-48`
- **Problem:** Poprawna logika z innym typem kontenera odpada.
- **Weryfikacja:** `merge_intervals` zwracające `[(1,6),(8,10),(15,18)]` → FAIL vs oczekiwane `[[1,6],...]`; wersja z `float` przechodzi.
- **Propozycja:** Porównanie semantyczne (`==` po normalizacji list↔tuple, ewentualnie `math.isclose` dla float).

### 7. Klucze `bug2` — silny bias polski, angielskie opisy odrzucane
- **Plik:** `prompts.json:79-80`, `bench_coding.py:52-58`
- **Problem:** Poprawne angielskie wyjaśnienia nie matchują żadnego klucza.
- **Weryfikacja:** m.in. „Removing elements during iteration causes skipped elements…", „Modifying a list during a for-loop is unsafe" → NIE; polskie „w trakcie iteracji" → OK. Wynik 2/4 z `results_coding.json` mógł wynikać z wariantu językowego lub wariancji modelu (re-run: 4/4 po polsku).
- **Propozycja:** Dodać klucze EN: `while iterating`, `during iteration`, `skip(s)? element`, `modify.*(during|while).*iterat`; rozważyć zapis pełnych odpowiedzi w JSON (jak w reasoning).

### 8. Klucze Z1 (rodzeństwo) — kolejność liczb ma znaczenie
- **Plik:** `prompts.json:19-20`, `bench_reasoning.py:20-28`
- **Problem:** `\b4\b.*\b3\b` wymaga „4 przed 3".
- **Weryfikacja:** „dziewczynek 3, chlopcow 4" → NIE; „chlopcow: 4, dziewczynek: 3" → OK.
- **Propozycja:** Osobno sprawdzać obecność 4 i 3 z kontekstem (`chlop`, `dziewcz`) bez narzucania kolejności.

### 9. `bench_numpredict.py` — `word_count()` ignoruje thinking przy overflow
- **Plik:** `bench_numpredict.py:37-38`, `_common.py:122-123`
- **Problem:** Przy `num_predict=1500` gpt-oss: 0 słów w `response`, 64 s — to realny overflow, ale metryka „słowa odpowiedzi" nie pokazuje zużycia budżetu na thinking (`eval_count` vs `word_count`).
- **Propozycja:** Raportować `thinking_words`, `eval_count`, `done_reason`; ewentualnie `response_empty=true`.

### 10. `unload()` połyka wszystkie wyjątki — brak gwarancji unload
- **Plik:** `_common.py:37-42`
- **Problem:** `except Exception: pass` — pierwszy test unload czasem zostawiał model w `/api/ps` (przed ponownym wywołaniem). Izolacja opiera się na cichym sukcesie.
- **Propozycja:** Logować błąd; po unload weryfikować `/api/ps`; ewentualnie retry z backoff (częściowo pokryte poll w `isolate`, ale nie w samym `unload`).

### 11. `bench_cost.py` — stała 45 W zafałszowuje bezwzględne kWh
- **Plik:** `bench_cost.py:26-33`
- **Problem:** Wzór wymiarowo poprawny (`W·s / 3_600_000 = kWh` ✓), ale 45 W to szacunek M1 Max GPU-bound. Inny chip / CPU-bound inference → inne kWh przy tym samym tok/s. Ranking przy stałej mocy OK, liczby bezwzględne — nie.
- **Propozycja:** Oznaczać wynik jako `estimated_kwh`; opcjonalnie import z `powermetrics`; osobne `BENCH_POWER_W` per model.

---

## DROBNY

### 12. Metryki `gen_tok_s` / `prompt_tok_s` — jednostki OK, `load_duration` wykluczony
- **Plik:** `_common.py:83-97`, `100-114`
- **Problem:** Brak buga. `eval_duration` w ns, dzielenie przez `1e9` daje poprawne tok/s; `load_duration` nie wchodzi do `eval_duration` (weryfikacja: load 8.0 s, eval 0.215 s, total ≈ suma).
- **Propozycja:** Brak zmiany kodu; ewentualnie komentarz o modelach thinking (→ finding #1).

### 13. `bench_speed.py` — warmup poprawnie odrzucony, mediana z 3 sensowna
- **Plik:** `bench_speed.py:36-49`
- **Problem:** Brak buga w logice. Warmup nie trafia do `rates`; mediana z 3 przebiegów działa (np. qwen 55.7/54.8/53.8).
- **Propozycja:** Rozważyć więcej przebiegów (5+) lub MAD/outlier drop dla devstral (7.7–9.3).

### 14. `--big` — `num_predict` podniesione do 256 (wcześniej 64)
- **Plik:** `bench_speed.py:71-73`
- **Problem:** Przy 64 tok/s było stabilne (spread 0.0), ale przy EOS przed limitem mediana jest krucha. Obecne 256 to poprawka.
- **Propozycja:** Sprawdzać `done_reason == 'length'`; raportować gdy `eval_count < num_predict`.

### 15. `prompt_tok_s` i `total_s` tylko z ostatniego przebiegu, nie z mediany
- **Plik:** `bench_speed.py:54-55`
- **Problem:** `gen_tok_s` = mediana z 3, ale `prompt_tok_s`/`total_s` z run #3 — niespójność raportu.
- **Propozycja:** Mediana także dla `prompt_tok_s` albo jawne `*_last_run`.

### 16. Weryfikacja izolacji jednorazowa (po warmup), nie per-run
- **Plik:** `bench_speed.py:40-43`
- **Problem:** Inny proces może doładować model w trakcie 3 pomiarów — niewykryte.
- **Propozycja:** `list_loaded()` przed każdym przebiegiem lub lock na czas benchmarku.

### 17. `isolate(target)` — parametr `target` nieużywany
- **Plik:** `_common.py:45`
- **Problem:** Wyładowuje wszystko, nie weryfikuje „tylko target". Mylące API, nie psuje pomiaru (warmup ładuje na nowo).
- **Propozycja:** Usunąć parametr albo po unload sprawdzać, że `target` jest jedyny w `/api/ps`.

### 18. `bench_numpredict.py` — `sys.argv[2-1]` działa, ale kruche
- **Plik:** `bench_numpredict.py:23-25`
- **Problem:** `python3 bench_numpredict.py MODEL` → domyślnie 1500/3000 OK. `MODEL abc` → crash `int()`. Wzorzec `N-1` myli przy czytaniu.
- **Propozycja:** `argparse`; walidacja `low < high`.

### 19. `extract_code()` — ogólnie OK, sensowne edge-case'y
- **Plik:** `bench_coding.py:21-29`
- **Problem:** Preferuje blok z `def`; bez fence zwraca cały tekst (może wywołać `exec error`). To ograniczenie metody, nie twardy bug.
- **Propozycja:** Odrzucać tekst bez `def` przed `exec`; opcjonalnie AST-parse.

### 20. `bench_coding` — brak zapisu treści odpowiedzi przy bug-find
- **Plik:** `bench_coding.py:94-95`
- **Problem:** W JSON tylko `"ok": false` — nie da się audytować false-negative/positive po fakcie (w reasoning jest `answer`).
- **Propozycja:** Dopisać `"answer": ...` do `details`.

### 21. Z2 bug-finding / reasoning — wynik 2/4 to głównie wynik modelu, nie wąskie klucze
- **Plik:** `prompts.json:79-80`, `results_reasoning.json:11-14`
- **Problem:** qwen na Z2 dostał NIE słusznie — odpowiedź „A jest lotrem" to błąd modelu, nie gradingu. Klucze łapią „sprzeczn/paradoks"; qwen ich nie użył. Re-run bug2: 4/4 po polskich opisach.
- **Propozycja:** Klucze rozszerzyć (finding #7); przy publikacji human eval (już w README).

---

## Podsumowanie priorytetów

| Priorytet | Finding | Wpływ na wyniki |
|-----------|---------|-----------------|
| 1 | Thinking tokens w `eval_count` (#1) | Fałszuje tok/s i koszt energii dla gpt-oss |
| 2 | Z4 false-positive `zmieni` (#2) | Zawyża reasoning score |
| 3 | Izolacja: `None`=sukces, timeout bez błędu (#3, #5) | Zaniża tok/s przy konkurencji VRAM |
| 4 | `:latest` vs nazwa modelu (#4) | Fałszywe flagi, nie psuje samych liczb |
| 5 | Strict `!=` w coding (#6) | Zaniża wynik kodowy |
| 6 | Klucze PL-only / kolejność Z1 (#7, #8) | Zaniża reasoning/coding przy innym sformułowaniu |

**Co jest poprawne:** wzór `gen_tok_s` (ns→s), wykluczenie `load_duration`, warmup odrzucony, `unload("", keep_alive=0)` działa na żywym API, wzór kWh w `bench_cost.py` wymiarowo poprawny.