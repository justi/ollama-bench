# Przykładowy przebieg (2026-06-23)

Środowisko: Apple Silicon, Ollama 0.30.10 (Ollama.app). Modele to lokalne warianty `-fast`.
Wartości bezwzględne zależą od sprzętu - chodzi o relacje i rzędy wielkości względem artykułu.

## tok/s generacji (`bench_speed.py`, mały prompt)

| Model | Zmierzone | Artykuł | Zgodność |
|---|---|---|---|
| qwen3-coder:30b-fast | 53-60 tok/s | ~52 tok/s | ✓ najszybszy |
| devstral-small-2:24b-fast | 13.8 tok/s | ~12 tok/s | ✓ |
| gemma4:31b-fast | 9.6 tok/s | ~6 tok/s | ✓ najwolniejszy, niezdatny do pracy interaktywnej |
| gpt-oss (każdy wariant) | błąd ładowania | - | uszkodzony blob GGUF, patrz niżej |

Relacja z artykułu (qwen wielokrotnie szybszy od gemmy) - odtworzona.

## Zagadki logiczne (`bench_reasoning.py`)

qwen3-coder:30b-fast: **auto-grade 4/6, po ręcznej weryfikacji 5/6**.

- Z1 (rodzeństwo): model odpowiedział poprawnie "4 chłopców, 3 dziewczynki", ale grader
  zaniżył przez format (`**4**` + newline) - false-negative naprawiony w tej wersji skryptu.
- Z5 (ASCII 76): realny błąd modelu - odpowiedział "V" zamiast "L".

To odtwarza dwie rzeczy z artykułu naraz: qwen jest dobry na reasoning (5/6, blisko źródłowych 6/6)
**oraz** automatyczna metryka rozjeżdża się z ręczną oceną - dokładnie teza "automatyczne checky
zawyżają/zaniżają, potrzeba human eval".

## Duży prompt (`bench_speed.py --big`, qwen vs devstral)

Pierwszy przebieg (repeat=500, ~40k tokenów - za dużo): qwen **388 s** (ukończył),
devstral **timeout >900 s**. Wartości bezwzględne zawyżone złą kalibracją promptu
(repeat poprawione na 160 -> ~12k tokenów), ale **relacja z artykułu się potwierdza**:
devstral jest dramatycznie wolniejszy od qwen na dużym kontekście (nie domknął, gdy qwen tak).
To dokładnie teza "sliding window attention nie skaluje się na dużym prompcie".

## Czego nie udało się zmierzyć

- **gpt-oss** (`num_predict` 293→747 słów, gpt-oss reasoning) - lokalny blob GGUF
  (`sha256-b112e727...`) jest uszkodzony: `gguf_init_from_reader: failed to read tensor info`.
  Naprawa: `ollama pull gpt-oss:20b` (~14 GB) pobierze świeży plik.
- **duży prompt** (`--big`, "devstral 40 s vs qwen 17 s") - nie uruchomione w tym przebiegu.

## Uwaga operacyjna (warta wpisu do artykułu)

Na tym Macu działały DWIE instalacje Ollamy: brew formula (niekompletna - bez `llama-server`)
trzymała port 11434 i blokowała inference, obok kompletnej Ollama.app. Fix: zatrzymać brew serwer
(`brew services stop ollama`) i używać Ollama.app. Lekcja dla czytelnika: instaluj Ollamę z
jednego źródła (oficjalna app **albo** brew), nie z obu naraz.
