# Wyniki benchmarku (2026-06-23)

Środowisko: Apple M1 Max 64 GB, Ollama 0.30.10. Skrypty przeszły audyt dwóch niezależnych
modeli (codex ×2 + grok, ~30 findings) - wszystkie krytyczne/ważne naprawione i zweryfikowane.
Pomiary: izolacja (1 model w pamięci), warmup + mediana z 3.

## KOD EXPERT (9 zadań codex) - RZETELNY RE-TEST n=3 na best configach (2026-06-24)

Dziewięć nietrywialnych zadań od codex (CSV, FIFO, scalanie przedziałów, ułamki, tokenizer,
mini-make/propagacja zmian, bankers rounding, stable merge, CIDR). Testy zweryfikowane
referencyjnymi rozwiązaniami. Configi przeszły review grok+codex przed testem.

Setup: każdy model na SWOIM best configu + poprawne sterowanie thinking (qwen36/north
`--think=false`, gpt-oss `--think=low`, qwen-coder/phi4/devstral bez thinking) + fair
`num_predict=3000` (patrz niżej) + **n=3, mediana + zakres** (jak consistency reasoningu).

| Model | przebiegi kod /9 | **mediana** | zakres | stabilność |
|---|---|---|---|---|
| **qwen3.6-best** (no-think) | 6,6,7 | **6** | 6-7 | dobra |
| **unsloth-q4xl-best** (3.5 Q4_K_XL) | 6,5,7 | **6** | 5-7 | średnia |
| **gpt-oss-best** (`--think=low`) | 6,4,7 | **6** | 4-7 | słaba (szum 3) |
| qwen-coder-best (nie-thinking) | 5,5,4 | **5** | 4-5 | dobra |
| north-best (no-think) | 3,4,4 | **4** | 3-4 | dobra |
| devstral-best (nie-thinking) | 4,4,4 | **4** | 4-4 | idealna |
| phi4-best (nie-thinking) | 2,3,5 | **3** | 2-5 | najgorsza (szum 3) |

(deepseek-r1 usunięty przed n=3: najwolniejszy ~4 tok/s + dno 4/9 + bez wygrywającej osi.)

ODKRYCIE 1 - num_predict=1500 zaniżał gadatliwe modele (false-negative przez ucięcie):
- Pierwotny benchmark hardcodował `num_predict=1500`. Dla zwięzłych modeli OK (kończą się
  naturalnie, `done_reason=stop` poniżej budżetu), ale unsloth jest gadatliwy (3500-6000 znaków,
  komentarze po polsku) i bił w sufit: `done_reason=length`, `eval_count=1500`, kod ucięty w
  połowie → SyntaxError = OBLANY, choć model był poprawny. Zmierzone (n=3 per task): stale_targets
  ucinane 2/3, bankers_cents 1/3.
- Skutek: unsloth dostał 3/9 (zaniżone), prawdziwa jakość przy fair 3000 = **6/9** (różnica 2 pkt).
- Naprawa: `--num-predict=N` + detekcja ucięcia (`done_reason=length` → flaga `TR!` + `[UCIETE]`).
  Po fair re-teście: zero ucięć u WSZYSTKICH modeli (`TR!`=0). Lekcja: równy budżet ≠ równa
  szansa; trzeba mierzyć `done_reason`, nie zakładać że limit nie wiąże.

ODKRYCIE 2 - ranking n=1 był MYLĄCY (szum losowania ±1-3 na zadaniach expert):
- Ten sam model swingował o 2-3 punkty między przebiegami (phi4: 2→3→5, gpt-oss: 6→4→7).
  Przy n=1 phi4 mógł wypaść 2 albo 5, gpt-oss 4 albo 7 - czysta loteria.
- Wcześniejszy n=1 ("qwen36 6 > qwen-coder=gpt-oss 5 > reszta 4") był BŁĘDNY w 3/7 pozycji:
  gpt-oss zaniżony (n=1: 5, mediana: 6), unsloth błędnie 3 (ucięcie, mediana: 6), phi4 niestabilny.
- Rzetelny obraz n=3: SZCZYT to TRÓJKA remisowa (mediana 6): **qwen3.6 = unsloth = gpt-oss**.
  Potem qwen-coder (5), north=devstral (4), phi4 (3). devstral najprzewidywalniejszy (4/4/4).

WNIOSEK: na osi poprawności kodu trudnego top jest remisowy (mediana 6: qwen3.6/unsloth/gpt-oss),
a różnice 1-punktowe niżej są w granicach szumu. Hyped unsloth quant (3.5 Q4_K_XL) DORÓWNUJE
Ollama 3.6 - ani lepszy, ani gorszy. Potrójna lekcja "mierz, nie zakładaj": (1) dobór zadań,
(2) konfiguracja modelu (thinking), (3) parametry benchmarku (num_predict) i liczba prób (n)
potrafią każda z osobna całkowicie zmyć ranking. Sam benchmark trzeba audytować jak mierzony obiekt.

## TABELA WSZECHSTRONNA: kod + reasoning + speed + energia (best configs, thinking OFF, 2026-06-24)

Wszystkie osie jakości z thinkingiem WYŁĄCZONYM (`--no-think`; gpt-oss `--think=low` - nie da
się w pełni wyłączyć). Kod = mediana n=3 /9. Reasoning = średnia n=3 /6 (zagadki logiczne).

| Model | kod med /9 | reasoning śr /6 | tok/s | kWh/1M | profil |
|---|---|---|---|---|---|
| **unsloth-q4xl-best** | **6** | **5.0** | 38.0 | 0.329 | jedyny mocny na OBU osiach |
| qwen-coder-best | 5 | 3.67 | **61.2** | **0.204** | koder + król efektywności |
| gpt-oss-best | **6** | 4.0* | 51.2 | 0.244 | kod-sufit + szybki (kod loteria) |
| qwen36-best | **6** | 3.0 | 44.9 | 0.278 | najlepszy kod, reasoning słaby BEZ thinking |
| north-best | 4 | 4.0 | 51.0 | 0.245 | szybki, średni wszędzie |
| devstral-best | 4 | 5.0 | 9.8 | 1.276 | reasoner, brutalnie wolny (6x energii) |
| phi4-best | 3 | **5.33** | 20.2 | 0.619 | najlepszy reasoning, najgorszy kod |

\* gpt-oss z `--think=low` (harmony - nie da się wyłączyć), więc jego reasoning ma minimalny thinking.

INWERSJA KOD↔REASONING (best model zależy od zadania - dosłownie):
- **phi4**: najgorszy kod (3) ↔ NAJLEPSZY reasoning (5.33).
- **qwen36**: NAJLEPSZY kod (6) ↔ najgorszy reasoning (3.0, thinking off).
- Dwa modele zamieniają się miejscami na dwóch osiach - dobór zadania całkowicie odwraca ranking.

CAVEAT (krytyczny dla uczciwości): qwen36/north to thinking-modele - ich reasoning ŻYJE w trybie
thinking. Reasoning mierzony z thinking OFF odbiera im główną broń: qwen36 3.0 to "qwen36 bez
mózgu reasoningowego". Z thinking ON skoczyłby wysoko (to jego projekt). Pomiar thinking-off jest
fair floor jednakowy dla wszystkich, ale SPECYFICZNIE zaniża thinking-modele na osi reasoningu.
Pełny obraz wymagałby drugiej tabeli reasoning z thinking ON (nie mierzona tutaj na życzenie).

WNIOSEK: z thinkingiem OFF unsloth-q4xl jest najbardziej ZBALANSOWANY (kod 6 + reasoning 5.0) -
hyped quant raz dany fair budżet okazuje się najwszechstronniejszy. qwen-coder wygrywa na
efektywności (kod 5, najszybszy+najtańszy). devstral/phi4 mocne TYLKO na reasoningu, drogo
(wolne). Ale ranking jest jednowymiarowy bez thinking-on reasoningu - patrz caveat.

## REASONING: thinking OFF vs ON - ile faktycznie dodaje myślenie (n=3, /6, 2026-06-25)

Twardy pomiar tezy "thinking pomaga reasoningowi". Thinking-modele (qwen36, north default;
gpt-oss `--think=high`) zmierzone n=3 z hojnym `num_predict=6000` + detekcją ucięcia.

| Model | OFF /6 | ON /6 | Δ thinking | wniosek |
|---|---|---|---|---|
| **qwen36-best** | 3.0 | **5.0** | **+2.0** | thinking ESENCJONALNY |
| north-best | 4.0 | **5.0** | +1.0 | thinking pomaga |
| gpt-oss-best | 4.0 (low) | 4.33 (high) | +0.33 | low→high marginalnie |
| phi4-best | **5.33** | - | non-thinking | i tak najlepszy reasoner |
| devstral-best | 5.0 | - | non-thinking | - |
| unsloth-q4xl-best | 5.0 | - | nothink wbity | - |
| qwen-coder-best | 3.67 | - | non-thinking | - |

DWIE TWARDE KONKLUZJE:
1. Thinking REALNIE pomaga reasoningowi, ale magnitude zależy od modelu: qwen36 +2.0 (z dna na
   czoło), north +1.0, gpt-oss tylko +0.33 (low→high). Teza potwierdzona, ale nie jest stała.
2. phi4 (5.33, BEZ thinking) wygrywa nawet z thinking-modelami na ich najlepszym trybie (5.0) -
   genuinie najlepszy reasoner, myślenie mu niepotrzebne.

Pomiar ujawnił też: na qwen36 q1 i gpt-oss q3 myślenie ucinało się NAWET przy 6000 tokenów
(flaga UCIETE) - thinking na tych zagadkach jest gigantyczny; ich wynik to dolna granica.

TABELA WSZECHSTRONNA POPRAWIONA (każdy model w NAJLEPSZYM trybie: kod=think off, reasoning=think on):

| Model | kod med /9 | reasoning /6 (best mode) | tok/s | kWh/1M | profil |
|---|---|---|---|---|---|
| **qwen36-best** | **6** | **5.0** (ON) | 44.9 | 0.278 | najlepszy wszechstronny (steruj thinkingiem) |
| **unsloth-q4xl-best** | **6** | **5.0** (off) | 38.0 | 0.329 | czołówka obu, ale wolniejszy + starsza 3.5 |
| qwen-coder-best | 5 | 3.67 | **61.2** | **0.204** | król efektywności, słabszy reasoning |
| gpt-oss-best | **6** | 4.33 | 51.2 | 0.244 | top kod + szybki, kod-loteria |
| north-best | 4 | 5.0 (ON) | 51.0 | 0.245 | szybki + dobry reasoning ON |
| phi4-best | 3 | **5.33** | 20.2 | 0.619 | najlepszy reasoner, najgorszy kod |
| devstral-best | 4 | 5.0 | 9.8 | 1.276 | reasoner, brutalnie wolny (6x energii) |

KOREKTA wcześniejszego wniosku: qwen36 NIE jest słaby na reasoningu - wyglądał tak TYLKO przez
wymuszony thinking off (3.0). W swoim trybie (thinking on) ma 5.0. Sterując thinkingiem PER
ZADANIE (off→kod, on→reasoning) qwen36 jest najlepszym wszechstronnym: czołówka OBU osi.
unsloth dorównuje (6+5.0) ale jest wolniejszy, starsza wersja i NIE umie przełączać (nothink
wbity). To finalne domknięcie tezy "thinking pomaga logice, ale psuje kod - steruj nim per zadanie".

## MACIERZ FINALNA: best configs, osie kod + speed/energia (n=3 kod + izolowany speed/energia, 2026-06-24)

Kod = mediana z n=3 (fair num_predict=3000). Speed = output tok/s, izolacja, mediana z 3 (rozrzut
0.1-4 tok/s - throughput stabilny, cała zmienność jest w jakości kodu). Energia = kWh/1M tokenów
output, moc 45 W (szacunek M1 Max; ranking odporny - różnice z tok/s, nie z mocy).

| Model | kod med (zakres) | tok/s | kWh/1M | h/1M | charakterystyka |
|---|---|---|---|---|---|
| **qwen-coder-best** | 5 (4-5) | **61.2** | **0.204** | 4.5 | król efektywności: najszybszy + najtańszy + stabilny |
| gpt-oss-best | **6** (4-7) | 51.2 | 0.244 | 5.4 | top kod ale loteria; szybki/tani z trójki |
| north-best | 4 (3-4) | 51.0 | 0.245 | 5.4 | szybki, ale kod słabszy |
| **qwen36-best** | **6** (6-7) | 44.9 | 0.278 | 6.2 | najlepszy kod STABILNY, średni speed |
| unsloth-q4xl-best | **6** (5-7) | 38.0 | 0.329 | 7.3 | top kod, wolniejszy + starsza 3.5 |
| phi4-best | 3 (2-5) | 20.2 | 0.619 | 13.8 | wolny + kod loteria - słaby |
| devstral-best | 4 (4-4) | 9.8 | 1.276 | 28.3 | najwolniejszy, 6x energii qwen-codera |

ROZSTRZYGNIĘCIE potrójnego remisu na kodzie (qwen36 = unsloth = gpt-oss, mediana 6):
- gpt-oss: najszybszy i najtańszy z trójki, ale kod to loteria (4-7).
- qwen36: najpewniejszy kod (6-7), średni speed - najlepszy gdy zależy na powtarzalności.
- unsloth: najwolniejszy z trójki + starsza wersja 3.5 - brak powodu by wybierać go nad qwen36.

WERDYKT PRAKTYCZNY:
- **qwen-coder = najlepszy ogólnie**: 61 tok/s, 0.204 kWh, stabilny; kod 5 to tylko -1 od szczytu.
  Top-tier płaci za 1 punkt kodu 20-50% więcej energii i czasu.
- **qwen36 = najwyższy PEWNY kod** (6-7). **gpt-oss = sufit kodu + szybkość, jeśli akceptujesz wariancję.**
- devstral tylko dla niszy reasoningu (6x energii!); phi4 wypadł słabo (wolny + loteria kodu).

BUG ZNALEZIONY W TRAKCIE (bench_speed.py): zmienna `think` w pętli main() była nadpisywana
przez kod komunikatu (`think = ""`), więc po PIERWSZYM modelu wszystkie kolejne dostawały
`"think": ""` → HTTP 400 i `BLAD`. Pierwszy model w każdym przebiegu był OK, reszta padała.
Oznacza to, że wcześniejsze multi-modelowe pomiary speed (poza pierwszym modelem) były
niewiarygodne. Fix: rename na `think_note`. Po naprawie wszystkie 7 modeli zmierzone.
Kolejna lekcja: kolizja nazw zmiennych cicho psuła pomiar - audytuj narzędzie, nie tylko wynik.

## KOD STANDARDOWY nie rozróżnia topów (łatwe i hard - wszyscy max)

Wszystkie modele 30B+ dają kod 8/8 (łatwe) ORAZ 9/9 (trudne: sliding window, histogram,
edit distance, coin change, trap water, word break). Nawet "hard" algorytmy LeetCode to dla
nich rutyna - są w danych treningowych. **Auto-testowalny kod algorytmiczny NIE dyskryminuje
topowych modeli lokalnych** - wszystkie perfekcyjne.

Co BY rozróżniało (i pokazał to MEGA_BENCHMARK doktoratu): REALNY kod, nie izolowane algorytmy.
Tam devstral dał 0/8 na 440-liniowym kontrolerze Rails (cross-file context), gpt-oss 55% - bo
to wymagało zrozumienia kontekstu, nie odtworzenia znanego algorytmu. Różnicują: debugowanie
realnego kodu wieloplikowego, nietypowe problemy spoza training data, analiza istniejącego kodu.
Tego NIE da się auto-testować (wymaga human eval / realnego repo) - to ta sama lekcja co
"benchmark != rzeczywistosc". W tabelach kolumna "kod" jest więc max u wszystkich i nie sortuje.

## TABELA MASTER - wszystkie modele, wszystkie osie (z prądem i czasem)

Sortowanie po szybkości. Prąd/czas liczone dla OUTPUT tokenów (widoczna odpowiedź, nie thinking).

| Model | output tok/s | czas h/1M | prąd kWh/1M | reasoning /6 | consist. | kod /8 |
|---|---|---|---|---|---|---|
| north-mini-code | 64.7* | 4.3 | **0.19** | 5.0 / 3.67* | 2 | 8/8 |
| qwen3-coder | 61.8 | 4.5 | 0.20 | 3.67 | 2 | 8/8 |
| qwen3.6 | 47* | 5.9 | 0.27 | 4.67 / 3.33* | 1 | 8/8* |
| gpt-oss | 22.6 | 12.3 | 0.55 | 5.0 | 0 | 8/8 |
| devstral | 12.4 | 22.4 | 1.01 | 5.33 | 1 | 8/8 |
| phi4 | 12.0 | 23.1 | 1.04 | 5.0 | 0 | 8/8 |
| deepseek-r1 | 4.0* | 69.4 | **3.13** | 5/6 / 4.33* | 1 | 8/8* |

Legenda: output = widoczne tok/s · czas h/1M = godzin na 1M output-tokenów · prąd kWh/1M przy
~45 W (pomnóż przez swoją cenę kWh dla zł) · reasoning = średnia ×3 (thinking pomaga) ·
consist = zakres (0 = przewidywalny) · kod /8 · `*` = z no-think.

Kluczowe z prądu/czasu:
- **16× rozpiętość zużycia prądu**: north 0.19 kWh/1M -> deepseek-r1 3.13 (4 tok/s = 69 h/1M!).
- **Energia jest odwrotnie proporcjonalna do szybkości** - wolny model zżera ~16× więcej prądu
  na ten sam output, nie tylko każe czekać.
- `*` u qwen3.6/r1: kod 8/8 TYLKO z no-think (z thinking 4/8); reasoning wtedy spada (trade-off).

---

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

## TABELA: thinking-modele z NO-THINK (think=False / --no-think)

WAŻNE: dla gpt-oss think=False jest IGNOROWANY (harmony hardcoded - tylko reasoning_effort
low/medium/high, nie zero; ollama issue #11751). Prawdziwy no-think tylko qwen36 i north.

| Model | output tok/s | reasoning (śr×3) | consistency | kod /8 | energia kWh/1M | thinking off? |
|---|---|---|---|---|---|---|
| north-mini-code-1.0 | **64.7** | 3.67 [5,3,3] | 2 | 8/8 | 0.19 | TAK |
| qwen36-unsloth | ~47 (eval; bug 400 w speed) | 3.33 [3,3,4] | 1 | 8/8 | ~0.27 | TAK |
| deepseek-r1-8k | ~4 (wolny; speed bug) | 4.33 [4,4,5] | 1 | 8/8 | ~3.1 | TAK |
| gpt-oss:20b | 15-22 | 4.0 [4,4,4] | 0 | 8/8 | ~0.7 | NIE (ignoruje think=False) |

Thinking ON vs OFF (gdzie no-think działa):

| Model | output ON→OFF | reasoning ON→OFF | kod ON→OFF |
|---|---|---|---|
| north | 28.7 → **64.7** (2.3x szybciej) | 5.0 → 3.67 (gorzej) | 8/8 → 8/8 |
| qwen36 (Qwen-distill) | ~17 → ~47 | ~4 → 3.33 | **4/8 → 8/8 (naprawione)** |
| deepseek-r1 (Qwen-distill) | ~1.5 → ~4 | 5/6 → 4.33 | **4/8 → 8/8 (naprawione)** |

Wnioski:
- **Thinking OFF = dużo szybciej** (north 2.3x) + **naprawiony kod u Qwen-distill** - OBA modele
  Qwen-distill (qwen3.6, deepseek-r1) miały kod 4/8 z thinking ON i 8/8 z OFF. Identyczny wzorzec:
  kod ginie w eksplozji myślenia, `extract_code` z response go nie łapie. To NIE słaby model -
  to thinking. north/gpt-oss myślą mniej, więc kod 8/8 zawsze.
- **ALE thinking OFF = gorszy reasoning** (north 5.0→3.67 - thinking realnie pomaga logice).
  Trade-off: thinking do reasoningu, no-think do kodu i szybkości.
- **gpt-oss: thinkingu NIE da się wyłączyć** (hardcoded w training; think=False ignorowany).
  Tylko minimalizacja przez reasoning_effort="low". To ograniczenie Ollama+gpt-oss, nie benchmarku.
- Runtime: dla wiernego sterowania thinkingiem (zwł. gpt-oss) trzeba llama.cpp llama-server z
  jinja `chat_template_kwargs.enable_thinking` - Ollama tego nie odwzorowuje spójnie. (do zrobienia)

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
