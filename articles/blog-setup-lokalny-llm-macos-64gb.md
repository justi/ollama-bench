# Setup lokalnego LLM na macOS z 64 GB RAM (krok po kroku)

64 GB RAM nie znaczy "załaduj największy model". Znaczy: dwa wyspecjalizowane modele i sporo wolnego, żeby macOS nie zaczął swapować. Poniżej kompletny setup na Apple Silicon z Ollamą - z gotowymi komendami i plikami Modelfile do skopiowania. Każda liczba wydajnościowa niżej jest zmierzona na działającym środowisku (Apple M1 Max 64 GB, Ollama 0.30.10) i odtwarzalna skryptami z repo podlinkowanego na końcu.

## Krok 0: zainstaluj Ollamę

```bash
brew install ollama
ollama --version    # sprawdź, że działa (>= 0.30)
```

Ollama uruchamia się sama w tle przy pierwszym `ollama run`. Jeśli chcesz stały serwer, odpal `ollama serve` w osobnym oknie.

## Zasada: dwa modele, nie jeden gigant

Pokusa jest oczywista: masz 64 GB, więc ładujesz jeden model 30B+ i koniec. Problem w tym, że żaden pojedynczy lokalny model nie jest dobry do wszystkiego - a to akurat zmierzyłem na ośmiu modelach. Lepszy układ to szybki koder do codziennej pracy plus drugi model na zadania wymagające rozumowania:

| Rola | Model | Rozmiar |
|---|---|---|
| Codzienna praca, generacja kodu | `qwen3-coder:30b` | ~18 GB |
| Algorytmy, rozumowanie | `gpt-oss:20b` | ~13 GB |
| **Razem** | | **~31 GB** |

Po pobraniu obu zostaje ~33 GB wolnego RAM (rozmiary z `ollama list`) - system oddycha, a w razie potrzeby doładujesz trzeci model on-demand. To rozmiary na dysku; w pamięci przy aktywnym kontekście bywa nieco więcej, dlatego margines się przydaje.

Dlaczego gpt-oss, a nie wyżej punktujący reasoner? To świadomy kompromis. Na zagadkach logicznych gpt-oss dał w teście 4.33/6 - mniej niż phi4 (5.33) czy devstral (5.0), ale oba są znacznie wolniejsze (~20 i ~10 tok/s wobec ~51 u gpt-oss), więc jako stała baza wychodzą drogo. Gdy liczy się sama jakość rozumowania ponad przepustowość, doładuj phi4 on-demand.

## Krok 1: pobierz modele bazowe

```bash
ollama pull qwen3-coder:30b    # ~18 GB
ollama pull gpt-oss:20b        # ~13 GB
```

To publiczne tagi z rejestru Ollamy - pobiorą się bez dodatkowej konfiguracji.

## Krok 2: zbuduj warianty "best"

Domyślne modele działają, ale parę parametrów warto dostroić: ustabilizować sampling i - dla modelu z trybem myślenia - podnieść limit generacji, żeby nie ucinał odpowiedzi. Robi się to plikiem Modelfile i komendą `ollama create`.

**qwen-coder-best** - stabilny sampling do codziennej pracy z kodem:

```
FROM qwen3-coder:30b
PARAMETER temperature 0.7
PARAMETER top_k 20
PARAMETER top_p 0.8
PARAMETER repeat_penalty 1.05
PARAMETER num_ctx 8192
```

```bash
ollama create qwen-coder-best -f configs/qwen-coder.best.Modelfile
```

**gpt-oss-best** - z podniesionym limitem generacji:

```
FROM gpt-oss:20b
PARAMETER temperature 0.3
PARAMETER num_predict 3000
PARAMETER num_ctx 8192
```

```bash
ollama create gpt-oss-best -f configs/gpt-oss.best.Modelfile
```

`ollama create` z istniejącego modelu bazowego jest błyskawiczne - nie kopiuje wag, tylko dopisuje manifest z twoimi parametrami.

**Steruj myśleniem per zadanie.** To najważniejsza lekcja z pomiarów. Modele z trybem myślenia (qwen3.6, north, gpt-oss) świetnie rozumują, gdy myślą - ale na KODZIE myślenie potrafi zepsuć wynik: kod ginie w eksplozji tokenów myślenia, a parser nie wyłapuje go z odpowiedzi. W teście qwen3.6 z thinkingiem ON dawał 4/8 na zadaniach kodowych, a z `--no-think` - 8/8. Ten sam model, dwa razy lepszy wynik tylko przez tryb. Dlatego: do kodu `--no-think`, do rozumowania zostaw thinking ON. Wyjątek: gpt-oss ma myślenie wbite na stałe (harmony) - nie wyłączysz go, możesz tylko zminimalizować przez `--think=low`.

## Dlaczego num_predict ma znaczenie

gpt-oss generuje "tokeny myślenia", zanim odpowie. Przy domyślnym, niskim limicie predykcji te tokeny zjadają cały budżet, zanim model dojdzie do faktycznej odpowiedzi - "thinking overflow". Zmierzyłem to na zadaniu wymagającym dłuższej odpowiedzi: przy `num_predict=1500` widoczna odpowiedź miała **0 słów** (cały limit poszedł na myślenie, `done_reason=length`, 1500 tokenów uciętych); po podniesieniu do `3000` ta sama odpowiedź urosła do **512 słów**. Czas wzrósł z ~64 do ~93 s - akceptowalna cena za to, że odpowiedź w ogóle się pojawia.

Limit generacji to nie detal. To dlatego wariant gpt-oss wyżej ma `num_predict 3000` - inaczej model z myśleniem potrafi oddać pustą odpowiedź.

## Czego nie ładować

Nie każdy model nadaje się na Apple Silicon jako stała baza:

- **devstral jako stała baza w narzędziu agentowym** - dobry reasoner, ale brutalnie wolny: ~9.8 tok/s generacji i dramatyczny spadek na dużym kontekście (ok. 40 s na prompcie ~12 tys. tokenów, gdzie qwen-coder robi to w ~17 s). Do tego ~6x więcej energii na ten sam output niż qwen-coder. Trzymaj go do rozumowania on-demand, nie jako bazę.
- **deepseek-r1** - kuszący jako reasoning-model, ale niepraktyczny na tym sprzęcie: ~1.5 tok/s widocznego outputu, kod słaby nawet z wyłączonym myśleniem (4/9 na trudnym zestawie), a przy domyślnym kontekście 128K zżera ~54 GB RAM i wywala się na 64 GB (trzeba zejść do `num_ctx 8192`). Energetycznie ~40x droższy od qwen-codera.

Uwaga o energii: tych kWh nie mierzyłem watomierzem - są wyliczone z tok/s przy założonej stałej mocy 45 W. Pewny jest więc ranking (wolniejszy model = proporcjonalnie więcej energii na ten sam output), niepewna sama wartość bezwzględna.

## Drobne, ale ważne ustawienia

- **Kontekst (`num_ctx`)** - w Modelfile zostawiłem 8192; wystarcza do większości pracy i oszczędza RAM (przycięcie dużego kontekstu zwalnia rzędu kilkunastu GB - np. zejście z 64K do 8K). Przetwarzasz długie pliki? Podbij do `32768` lub `65536` - masz zapas pamięci.
- **Keep-alive** - model trzymany w pamięci startuje natychmiast. Wydłuż czas, żeby nie płacić za przeładowanie przy każdym wywołaniu:

```bash
OLLAMA_KEEP_ALIVE=30m ollama serve
```

- **Ollama w sieci lokalnej** - żeby uderzać do modelu z innej maszyny w domu, uruchom serwer na wszystkich interfejsach (domyślnie nasłuchuje tylko lokalnie):

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

## Test końcowy

Sprawdź, że oba warianty odpowiadają:

```bash
ollama run qwen-coder-best "Napisz funkcję w Pythonie sprawdzającą, czy liczba jest pierwsza."
ollama run gpt-oss-best "Rozwiąż zagadkę logiczną: trzy osoby, dwa kapelusze..."
```

Jeśli oba zwracają sensowną odpowiedź, masz działający dwumodelowy setup.

## Wniosek

Na 64 GB Maca optymalny układ to nie jeden największy model, tylko para: szybki koder jako baza (~19 GB) plus drugi model do rozumowania (~14 GB), razem ~33 GB i sporo wolnego. Ale najważniejsza lekcja z pomiarów jest inna: nie ma jednego "najlepszego" modelu - jest najlepszy do danego zadania, i to dosłownie - model z czołówki na kodzie potrafił wypaść najsłabiej na rozumowaniu, i odwrotnie. Pobierz publiczne modele bazowe, dostrój je krótkim Modelfile, steruj myśleniem per zadanie (off do kodu, on do logiki), podnieś `num_predict` tam, gdzie model myśli, i nie rób stałej bazy z modelu, który na Apple Silicon ledwo generuje. Sprzęt masz dobry - chodzi o to, żeby go nie zmarnować na jeden przeładowany model.

---

*Wszystkie liczby zmierzono na Apple M1 Max 64 GB, Ollama 0.30.10, i są odtwarzalne: pełne wyniki wszystkich osi (`RESULTS.md`), configi modeli (`configs/`), zadania testowe (`prompts.json`) i skrypty pomiarowe (`bench_*.py`) leżą w repozytorium [ollama-bench](https://github.com/justi/ollama-bench). Twoje wartości bezwzględne będą inne (zależą od sprzętu, wersji Ollamy i kwantyzacji) - chodzi o odtworzenie rzędów wielkości i relacji.*
