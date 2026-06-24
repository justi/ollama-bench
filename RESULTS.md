# Wyniki benchmarku (2026-06-23)

Środowisko: Apple M1 Max 64 GB, Ollama 0.30.10. Skrypty przeszły audyt dwóch niezależnych
modeli (codex ×2 + grok, ~30 findings) - wszystkie krytyczne/ważne naprawione i zweryfikowane.
Pomiary: izolacja (1 model w pamięci), warmup + mediana z 3.

## ETAP 1 - FAIR: wszystkie modele @ temp 0.7 (model vs model)

Porównanie przy JEDNEJ temperaturze - eliminuje różnice configu, pokazuje sam model. Patrz CONFIG.md.

| Model | output tok/s | eval tok/s | reasoning (śr×3) | consistency | kod /8 |
|---|---|---|---|---|---|
| qwen-coder-t07 | **61.7** | 61.7 | 3.33 [2,4,4] | 2 | 8/8 |
| gpt-oss-t07 | 38.1 | 53.9 | 4.33 [5,4,4] | 1 | 8/8 |
| north-t07 | 28.7 | 38.5 | 5.0 [6,4,5] | 2 | 8/8 |
| phi4-t07 | 10.9 | 10.9 | **5.0 [5,5,5]** | **0** | 8/8 |
| qwen36-t07 | 8.5 | 38.0 | 4.67 [5,5,4] | 1 | **4/8** |
| devstral-t07 | 8.1 | 8.1 | 5.0 [5,6,4] | 2 | 8/8 |

Wnioski (przy RÓWNEJ temp 0.7):
- **Kod: 5 z 6 modeli = 8/8.** Tylko qwen3.6 słaby (4/8) - i to NIE wina temperatury (temp 1 też
  dawało 4/8). qwen3.6 (model OGÓLNY) jest gorszy na kodzie niż dedykowani koderzy. Potwierdzone fair.
- **qwen3.6 reasoning naprawił się** z temp 1 (3.33) na temp 0.7 (4.67) - poprzedni wynik był niefair
  przez za wysoką temperaturę. Fair temp pokazuje przyzwoity reasoning qwen3.6.
- **phi4 najlepszy reasoning (5.0, zakres 0 = idealnie stabilny)** = devstral = north. qwen-coder
  najsłabszy (3.33) - koder ma słaby reasoning z natury.
- **Output: qwen-coder najszybszy (61.7).** qwen3.6 myśli ogromnie (3573 zn!) → output 8.5 mimo eval 38.
- Najlepszy wszechstronny fair: north (28.7 + 5.0 + 8/8) albo qwen-coder (61.7 + 8/8, słaby reasoning).

## ETAP 2 - BEST PARAMS PER MODEL (tylko jakość: kod + reasoning)

Każdy model w najlepszej formie (gpt-oss temp 0.3+np3000, qwen3.6 temp 0.3+top_p0.9, reszta natywna).
Bez osi zależnych od configu (speed/energia).

| Model | reasoning (śr×3) | consistency | kod /8 |
|---|---|---|---|
| devstral (natywny) | **5.33** [6,5,5] | 1 | 8/8 |
| gpt-oss-best (t0.3+np3000) | 4.67 [5,5,4] | 1 | 8/8 |
| north (natywny) | 4.33 [4,5,4] | 1 | 8/8 |
| qwen36-best (t0.3+topp0.9) | 4.0 [4,3,5] | 2 | **5/8 (gen 2/5)** |
| qwen-coder (natywny) | 3.67 [3,4,4] | 1 | 8/8 |
| phi4 (natywny) | 3.33 [2,6,2] | **4 (chaos!)** | 8/8 |

### KOREKTA (po teście z thinking OFF - wkład usera, config z forum)

**Wniosek "qwen3.6 słaby kod = model" BYŁ BŁĘDNY - to był THINKING, nie model.**

| qwen3.6 config | kod /8 | generacja |
|---|---|---|
| thinking ON (temp 1 / 0.7 / 0.3) | 4-5/8 | **2-3/5** |
| **NO-THINK + params unsloth** (temp 0.7, top_p 0.8, top_k 20, min_p 0, presence 1.5) | **8/8** | **5/5** |

Z thinking ON qwen3.6 wpadał w eksplozję myślenia (3573 zn) - kod chował się w polu `thinking`
albo był ucinany, więc `extract_code` z `response` go nie łapał. `think=False` (Ollama API)
naprawił wszystko: qwen3.6 pisze kod tak dobrze jak dedykowani koderzy. **Testowałem go w
najgorszej formie, nie najlepszej.** (reasoning bez zmian: 3.67 - szum; tam thinking nie psuł).

Lekcja: thinking-modele do KODU testuj z `--no-think` - inaczej kod ginie w thinking i wynik
jest fałszywie zaniżony. To dotyczy qwen3.6 ekstremalnie (3573 zn myślenia); gpt-oss/north mniej.

### KONKLUZJA obu etapów (skorygowana)

1. **Jakość KODU większości modeli jest stabilna (8/8), ALE u thinking-modeli zależy od trybu.**
   qwen-coder, gpt-oss, devstral, north, phi4 → 8/8 zawsze. qwen3.6 → 8/8 TYLKO z thinking OFF
   (z ON ginie w myśleniu). Czyli "typ modelu" to za mało - trzeba też właściwy tryb thinking.

2. **"Best params" bywa mitem.** phi4 @ natywnej temp wyszedł GORSZY i chaotyczny (3.33, [2,6,2],
   zakres 4) niż @ wymuszonej 0.7 (5.0, [5,5,5], zakres 0). "Zostaw natywne" nie zawsze wygrywa.

3. **Reasoning jest zaszumiony (±1-2); parametry nie dają pewnej poprawy.** qwen3.6 temp 0.7 (4.67) >
   temp 0.3 (4.0) na reasoning - mimo że temp 0.3 to ustalenie usera dla TOOL CALLING (inny cel).
   devstral lekko najlepszy reasoning (5.33) w obu etapach.

4. **Praktyczny wybór niezmienny po obu etapach:** do KODU dowolny z piątki (qwen-coder najszybszy,
   north najlepszy kompromis); qwen3.6 NIE do kodu (jego siła to polski/pipeline, nie mierzone tu).

---

## Szybkość: output tok/s vs eval tok/s (zestaw fast)

**Najważniejsze odkrycie audytu (grok #1):** dla modeli z trybem myślenia `eval_count` liczy
tokeny THINKING, nie tylko widoczny output. Surowy tok/s zawyża realną szybkość gpt-oss.

| Model | output tok/s | eval tok/s (surowy) | uwaga |
|---|---|---|---|
| qwen3-coder:30b-fast | **61.8** | 61.8 | brak thinking |
| gpt-oss-fast | **15.1** | 54.5 | ~72% generacji to myślenie (352 zn output / 915 zn think) |
| deepseek-fast | 14.0 | 14.0 | brak thinking |
| devstral-small-2:24b-fast | 12.4 | 12.4 | brak thinking |

gpt-oss NIE jest "drugi najszybszy" - jego widoczny output (15.1) jest na poziomie najwolniejszych.
Surowy ranking eval (qwen >> gpt-oss > deepseek > devstral) to artefakt thinking-tokenów.

Zestaw default (eval tok/s, output gpt-oss analogicznie niższy): qwen 54.8, gpt-oss 48.1,
deepseek 10.4, devstral 8.9.

## Reasoning = logika (poprawiony grader: anti-klucze, Z1 AND, LaTeX, diakrytyka)

| Model | fast | default | uwaga |
|---|---|---|---|
| devstral | **6/6** | (usunięty) | +1 po naprawie diakrytyki |
| gpt-oss | 5/6 | 5/6 | bez zmian |
| qwen3-coder | 3/6 | 3/6 | fast spadł 4→3 (nondeterminizm) |
| deepseek | (usunięty) | (usunięty) | stary auto 3/2, dolne oszacowanie |

**Re-grade poprawionym graderem NIE potwierdził uniwersalnego "+1".** devstral wzrósł (5→6
przez diakrytykę), ale qwen SPADŁ (4→3) - to nondeterminizm (temp 0.7) daje **±1 szum** między
przebiegami, który przykrywa efekt gradera. Wniosek: reasoning auto-grade to przybliżenie z
szumem ±1; rzetelnie wymaga uśrednienia wielu przebiegów + human eval (meta-teza znów).
deepseek i devstral:24b default usunięto dla miejsca - ich reasoning nie był re-mierzony.

## Reasoning: ŚREDNIA + CONSISTENCY (`--runs 3`)

Pojedynczy przebieg ma szum ±1 (temp 0.7). Trzy przebiegi dają średnią (prawdziwsza umiejętność)
i ZAKRES (consistency - przewidywalność modelu).

| Model | przebiegi | średnia /6 | zakres (consistency) |
|---|---|---|---|
| devstral-small-2:24b-fast | [6,6,6] | **6.0** | **0** (idealnie stabilny) |
| gpt-oss-fast | [5,5,5] | 5.0 | **0** (idealnie stabilny) |
| north-mini-code-1.0 | [4,5,5] | 4.67 | 1 |
| phi4:14b | [5,4,4] | 4.33 | 1 |
| qwen3-coder:30b-fast | [3,5,3] | 3.67 | 2 (chaotyczny) |
| deepseek-r1-8k | (1 przebieg, 5/6) | ~5 | niemierzone (za wolny na N) |

Tryb N PRZEMEBLOWAŁ ranking - dowód wartości:
- **phi4 "6/6" było szczęśliwym strzałem** - realnie 4.33 (waha 4-5). Pojedynczy przebieg wpisałby
  do macierzy fałszywego lidera reasoning.
- **devstral to prawdziwy lider reasoning: 6.0 I idealnie stabilny.** Najlepsza średnia + zerowy
  rozrzut = model, na którym można polegać.
- **consistency to niezależny sygnał:** qwen podwójnie słaby (niska średnia 3.7 + największy
  rozrzut 2 = loteria); devstral/gpt-oss podwójnie dobre (wysokie + stabilne). Sama średnia tego
  nie pokaże - chaotyczny model jest gorszy do produkcji niż przewidywalny o tej samej średniej.

## Kod = generacja (auto-test) + bug finding

| Model | fast | default |
|---|---|---|
| qwen3-coder | 8/8 | 8/8 |
| gpt-oss | 8/8 | 8/8 |
| devstral | 8/8 | 7/8 (kod 4/5) |
| deepseek | 7/8 | 8/8 |

Po naprawie bug2 (klucze EN, grok #7): gpt-oss 7→8/8, deepseek default 8/8 - wcześniej ich
angielskie opisy bugu były odrzucane. deepseek-coder słaby na logice, ale na KODZIE 7-8/8.

## Energia (kWh / 1M tokenów OUTPUT, zestaw fast, ~45 W)

| Model | kWh/1M | godzin/1M |
|---|---|---|
| qwen-fast | **0.20** | 4.5 |
| gpt-oss-fast | 0.83 | 18.4 |
| deepseek-fast | 0.89 | 19.8 |
| devstral-fast | 1.01 | 22.4 |

gpt-oss energia liczona dla OUTPUT (15.1 tok/s) wzrosła z ~0.24 do 0.83 - bo na 1M widocznych
tokenów generuje ~3.6× więcej (z myśleniem). To realny koszt thinking.

## MACIERZ DECYZYJNA: output × reasoning × consistency × kod × energia (fast)

| Model | output tok/s | reasoning (śr.) | consistency | kod /8 | energia kWh/1M |
|---|---|---|---|---|---|
| qwen-fast | **61.8** (1.) | 3.67 | 2 (chaos) | 8/8 | **0.20** (1.) |
| gpt-oss-fast | 15.1 (2.) | 5.0 | **0** (stabilny) | 8/8 | 0.83 (2.) |
| deepseek-fast | 14.0 (3.) | (usunięty) | - | 7/8 | 0.89 (3.) |
| devstral-fast | 12.4 (4.) | **6.0** | **0** (stabilny) | 8/8 | 1.01 (4.) |

(reasoning po poprawionym graderze; ±1 szum przez nondeterminizm temp 0.7)

Wnioski końcowe (po audycie - inne niż przed):
- **qwen-fast dominuje wydajność:** ~4× szybszy widoczny output niż reszta i 4-5× tańszy
  energetycznie, przy kodzie 8/8. Słabszy reasoning (4/6) nie szkodzi przy kodzie. Do
  codziennej pracy z kodem i dużego wolumenu - bezkonkurencyjny.
- **gpt-oss / devstral - najwyższa jakość (5/6 + 8/8), ale drogo:** efektywny output ~12-15 tok/s
  i 4-5× energii qwena. Wybierasz je, gdy jakość > przepustowość.
- **gpt-oss płaci thinkingiem:** ta sama jakość co devstral, ale eval 54 maskuje, że widoczny
  output to 15 tok/s. Jego przewaga "szybki I dobry" zniknęła po rozdzieleniu metryk.
- **deepseek-fast - najsłabszy ogólnie:** reasoning 3/6, kod 7/8, wolny, drogi. Na czysto
  programistycznych zadaniach (kod 7-8/8) bywa OK, ale qwen robi to szybciej, taniej i lepiej.

Najważniejsza lekcja: bez audytu (grok #1) macierz fałszywie pokazywała gpt-oss jako "najlepszy
kompromis szybkość+jakość". Po rozdzieleniu output/eval tok/s realny wybór to: **qwen do
przepustowości, gpt-oss/devstral do jakości** - a thinking ma mierzalną cenę w czasie i energii.

## MACIERZ DECYZYJNA: zestaw DEFAULT (publiczne tagi)

| Model | output tok/s | reasoning (śr.) | consistency | kod /8 | energia kWh/1M |
|---|---|---|---|---|---|
| qwen3-coder:30b | **57.1** (1.) | 4.67 | 1 | 8/8 | **0.22** (1.) |
| gpt-oss:20b | 22.6 (2.) | 4.67 | 1 | 8/8 | 0.55 (2.) |
| deepseek-coder:33b | 14.4 (3.) | 2/6* | n/d | 8/8 | 0.87 (3.) |
| devstral:24b | 11.4 (4.) | 5/6* | n/d | 7/8 | 1.10 (4.) |

(* 1 przebieg - model usunięty dla miejsca, consistency niemierzona. UWAGA: qwen "fast" i
"default" mają IDENTYCZNY sampling - temp 0.7, top_k 20, top_p 0.8, repeat 1.05 (jedyna różnica:
num_ctx; patrz Modelfile.qwen-fast). Różnica reasoning 3.67 vs 4.67 to NIE efekt wariantu, tylko
NONDETERMINIZM tego samego modelu - dwie próbki z tego samego rozkładu, w granicach szumu ±1.)

Obraz spójny z fast - qwen dominuje wydajność, gpt-oss/devstral wygrywają jakością.
Różnice fast vs default:
- gpt-oss DEFAULT ma WYŻSZY output (22.6) niż fast (15.1) - default myśli mniej (thinking
  653 zn vs fast 915 zn). Wariant fast paradoksalnie więcej rozumuje na tym prompcie.
- qwen fast szybszy (61.8 vs 57.1) i odrobinę lepszy reasoning (4/6 vs 3/6) - częściowo
  nondeterminizm (temp 0.7).
- deepseek default kod 8/8 (fast 7/8), devstral default kod 7/8 (fast 8/8) - wariancja modelu.
- We wszystkich przypadkach gpt-oss to jedyny thinking-model: output realnie << eval.

## MACIERZ: NOWE MODELE 2026 (dograne na życzenie)

| Model | output tok/s | reasoning (śr.) | consistency | kod /8 | energia kWh/1M |
|---|---|---|---|---|---|
| north-mini-code-1.0 | **43.6** | 4.67 | 1 | 8/8 | **0.29** |
| phi4:14b | 12.0 | 4.33 | 1 | 8/8 | 1.04 |
| deepseek-r1-8k | ~1.5 | 4.67 | 1 | 4/8 | 8.33 |

(reasoning po RĘCZNEJ weryfikacji + naprawie gradera: auto-grade zaniżał, bo nie rozumiał
LaTeX `\frac{2}{3}` ani polskich znaków `chłop` vs klucz `chlop`. r1 auto 3/6 -> realnie 5/6;
phi4 auto 5/6 -> 6/6. north-mini-code: Cohere 30B/3B MoE; phi4: Microsoft 14B; deepseek-r1:
32B, `num_ctx 8192` bo domyślne 128K = 54 GB RAM = crash na 64 GB)

Odkrycia:
- **north-mini-code WYPEŁNIA LUKĘ "szybki I dobry":** output 43.6 (2. po qwenie) + reasoning 5/6
  + kod 8/8 + tani (0.29). Lepszy wszechstronny niż gpt-oss, który ma output 15 przez thinking.
- **phi4 (14B, 9 GB) - rewelacja:** reasoning **6/6 (najlepszy ze wszystkich)** + kod 8/8, przy
  połowie rozmiaru dużych modeli. Wolniejszy (12 tok/s), ale jakościowo bezkonkurencyjny w klasie.
- **deepseek-r1 - dobry reasoning (5/6), ale niepraktyczny:** jako reasoning-model logika trzyma
  (auto-grade zaniżył do 3/6 przez LaTeX), ALE kod słaby (4/8, generacja 2/5), niepraktycznie
  wolny (4 tok/s eval, ~1.5 output) i pamięciożerny. Energia 8.33 kWh/1M (~40× qwena). Reasoning
  go nie ratuje - na tym sprzęcie nie nadaje się do codziennej pracy.
- **Lekcja o graderze:** Z1 zaniżał WSZYSTKIE modele (każdy pisał "chłopców" z ł). Reasoning
  fast/default (qwen/gpt-oss/devstral) z wcześniejszych przebiegów też prawdopodobnie o ~1 za
  nisko - auto-grade to dolne oszacowanie; przy publikacji potrzebny human eval (kolejny dowód
  meta-tezy "metryka != ocena").

## qwen3.6 vs qwen3-coder (na życzenie: czy nowsza generacja pomaga?)

| Oś | qwen3.6:35b-a3b-fast | qwen3-coder:30b-fast |
|---|---|---|
| output tok/s | 16.9 (thinking) | **61.8** |
| eval tok/s | 49.5 | 61.8 |
| reasoning (śr×3) | 3.33 [3,3,4] | 3.67 [3,5,3] |
| consistency | 1 | 2 |
| kod /8 | 4/8 (gen 2/5) | **8/8** |
| energia kWh/1M | 0.74 | **0.20** |

**[OBALONE później - patrz KOREKTA w sekcji ETAP 2: kod qwen3.6 4/8 wynikał z thinking ON,
nie z modelu. Z `--no-think` + params unsloth qwen3.6 daje kod 8/8 (generacja 5/5).]**

**Wniosek (przy thinking ON, czyli na ZŁYM configu): nowsza generacja nie pomaga na kodzie.** qwen3.6
(36B, gen 3.6, OGÓLNY - pod PL-tech pipeline) przegrywa z qwen3-coder (30B, dedykowany KODER)
na wszystkich osiach benchmarku kodowego:
- **kod 4/8 vs 8/8** - qwen3.6 nie napisał połowy funkcji; koder to jego domena, nie qwen3.6.
- **output 16.9 vs 61.8** - qwen3.6 to thinking-model (65% generacji = myślenie), coder czysty.
- **energia 3.6× droższa** - thinking spowalnia widoczny output.
Lekcja: "nowszy i większy" nie wygrywa automatycznie - liczy się dopasowanie typu do zadania.
qwen3.6 błyszczy tam, gdzie go zoptymalizowano (polski/pipeline), nie w benchmarku kodowym EN.

## Ranking WSZECHSTRONNY (wszystkie 3 zestawy razem)

1. **north-mini-code** - szybki (43.6) + 5/6 + 8/8 + tani. Nowy lider wszechstronny.
2. **qwen-fast** - najszybszy (61.8) i najtańszy, kod 8/8, ale słabszy reasoning (4/6). Król wydajności.
3. **phi4** - NAJLEPSZA jakość (reasoning 6/6 + kod 8/8), i to w 14 B! Ale wolny (12 tok/s). Gdy liczy się jakość, nie przepustowość.
4. **gpt-oss / devstral** - jakość 5/6 + 8/8, ale efektywnie wolne (output 12-15) i drogie.
5. **deepseek-r1** - dobry reasoning (5/6), ale odpada: słaby kod (4/8), bardzo wolny, pamięciożerny.

## Metodologia (dlaczego liczbom można ufać)

- **Load wykluczony:** tok/s z `eval_count/eval_duration` (ns); `load_duration` osobno.
- **Output vs eval:** dla modeli thinking rozdzielone (`response_tok_s_est` vs `eval_tok_s`).
- **Izolacja:** 1 model w pamięci (poll `/api/ps` aż pusto); bez tego deepseek/devstral były
  zaniżone (memory pressure). Brak potwierdzonej izolacji = liczba oznaczona jako niepewna.
- **Warmup + mediana z 3:** cold start zaniżał qwen; mediana zjada outliery.
- **Grading audytowany:** anti-klucze (sprzeczne rozumowanie), grupy AND (Z1), klucze PL+EN,
  normalizacja typów w auto-teście kodu, pełne odpowiedzi zapisywane do ręcznego audytu.
