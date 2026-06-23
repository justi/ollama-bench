# Konfiguracja benchmarku - dwa etapy

Cel: rozdzielić "który MODEL jest lepszy" (etap 1, równe warunki) od "jak dobrać model do
zadania w jego najlepszej formie" (etap 2, optymalne parametry per model).

## ETAP 1 - FAIR (model vs model, ta sama temperatura)

Wszystkie modele przebudowane z JEDNĄ wspólną temperaturą, by porównać same modele, nie configi.

- **Wspólna temperatura: 0.7**
  - NIE 0: gpt-oss wpada w 100% pętli (zmierzone w small-models-local-setup/mit5_report.md).
  - NIE 1.0: za chaotyczne (qwen reasoning skacze 3-5).
  - 0.7 = rozsądny środek, uczciwa wspólna podstawa.
- **Pozostałe parametry:** num_ctx 8192 (oszczędność RAM), reszta natywna per model.
- **Sufiks wariantów: `-t07`** (np. `qwen-coder-t07`).

### Modele w etapie 1 (te, co są teraz w tabeli)
- qwen3-coder:30b
- gpt-oss:20b
- devstral (z devstral-small-2:24b-fast jako baza - default usunięty)
- north-mini-code-1.0
- phi4:14b
- qwen3.6:35b-a3b

### Pominięte (przegrały wcześniej, usunięte z dysku)
- deepseek-coder, deepseek-r1 (wolne, słaby kod)
- gemma (najwolniejsza, niezdatna)
- devstral:24b default (najwolniejszy)

### UWAGA o thinking
temp ujednolica sampling, ale NIE wyłącza thinking. gpt-oss, north-mini-code, qwen3.6 to
thinking-modele - ich output tok/s liczony osobno (response vs eval). qwen-coder i phi4 bez
thinking. To cecha modelu, nie configu - zaznaczane w wynikach.

## ETAP 2 - BEST PER MODEL (każdy w najlepszej formie)

Każdy model ze swoimi NAJLEPSZYMI parametrami (z ustaleń w small-models-local-setup) - badamy
TYLKO jakość (kod + reasoning), bez osi zależnych od configu (szybkość/energia).

| Model | najlepsze parametry | źródło ustalenia |
|---|---|---|
| qwen3.6 | temp 0.3, top_p 0.9 | mit5_report: 6.7%→0% pętli |
| gpt-oss | temp 0.3, num_predict 3000 | MEGA_BENCHMARK: num_predict=3000 potwierdzone |
| qwen3-coder | temp 0.7 (default, no-think do szybkości / thinking do jakości algorytmów) | RAPORT_EXTREME |
| devstral | temp natywny | MEGA_BENCHMARK |
| north-mini-code | temp natywny (MoE coder) | - |
| phi4 | temp natywny | - |

Badane w etapie 2: tylko bench_coding + bench_reasoning (--runs 3). Bez speed/energia (te
zależą od configu, nie od jakości modelu).
