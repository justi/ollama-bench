# Ten sam przełącznik psuje kod i ratuje logikę

Wziąłem jeden lokalny model, qwen3.6, i przepuściłem przez ten sam zestaw zadań kodowych dwa razy. Raz dostał 4/8. Drugi raz 8/8. Nie zmieniłem ani promptu, ani temperatury, ani wersji modelu. Zmieniłem jeden przełącznik: thinking.

To nie ciekawostka. To najważniejsza praktyczna lekcja z całego benchmarku siedmiu lokalnych modeli na M1 Max: thinking - tryb, w którym model "myśli" w ukrytym bloku przed właściwą odpowiedzią - na kodzie szkodzi, a na logice pomaga. Nie ustawiasz go raz na stałe. Sterujesz nim per zadanie.

## Dlaczego thinking psuje kod

Model z włączonym thinkingiem najpierw generuje rozumowanie, dopiero potem odpowiedź - i rozbija wyjście na dwa pola: `thinking` (myślenie) i `response` (właściwa odpowiedź). Przy qwen3.6 to rozumowanie potrafiło mieć 3573 znaki. Na zadaniu kodowym efekt był zabójczy na dwa sposoby: kod albo lądował w polu `thinking` (a narzędzie czytało tylko `response`, więc go nie widziało), albo był ucinany w połowie, gdy myślenie zjadało budżet tokenów. Wynik: 4/8, "słaby koder".

Z `--no-think` ten sam model pisze kod od razu, czysto, i kończy z 8/8 - na poziomie dedykowanych koderów. Czyli testowałem go w najgorszej formie, a wniosek "qwen3.6 słabo koduje" był po prostu nieprawdą o modelu - prawdą o złym trybie.

I to nie był jeden feralny model. Dokładnie ten sam wzorzec dał deepseek-r1: 4/8 z thinkingiem, 8/8 bez. Oba wywodzą się z tej samej rodziny - modeli destylowanych z Qwena - i oba ginęły w identyczny sposób. To cecha rodziny, nie wypadek przy pracy. Modele, które myślą mniej - north, gpt-oss - miały kod stabilny niezależnie od trybu.

## Dlaczego thinking ratuje logikę

Teraz druga strona. Wyłącz thinking i zmierz zagadki logiczne - logika pada.

qwen3.6 na logice: 3.0/6 z thinkingiem wyłączonym, 5.0/6 z włączonym. Plus dwa punkty z jednego przełącznika. north: 4.0 do 5.0. To nie szum - to systematyczny zysk. Thinking realnie pomaga rozumowaniu, bo zadanie logiczne właśnie tego wymaga: rozpisania kroków przed odpowiedzią.

Z jednym zastrzeżeniem, które warto znać: zysk nie jest stały. qwen3.6 dostał +2.0 (przeskok z dna stawki na czoło), north +1.0, a gpt-oss tylko +0.33 (z poziomu "low" na "high"). Ile dokładnie dołoży thinking, zależy od modelu - ale kierunek jest zawsze ten sam.

## Dwa wyjątki, które warto znać

gpt-oss nie pozwala wyłączyć thinkingu w ogóle. Jego architektura ma myślenie wbite na stałe - możesz je tylko zminimalizować do poziomu "low", nigdy zgasić. To ograniczenie konkretnego modelu, nie metody. Jeśli zależy ci na pełnej kontroli thinkingu, to argument przeciw gpt-oss.

Drugi wyjątek jest ciekawszy. Najlepszy w logice w całej stawce okazał się phi4 - z wynikiem 5.33/6, i to BEZ żadnego thinkingu (to model nie-thinking). Bije nawet thinking-modele na ich najlepszym trybie (5.0). Czyli myślenie pomaga logice, ale nie jest jej warunkiem koniecznym: dobry model może rozumować i bez osobnego bloku myślenia.

## Thinking ma cenę: szybkość

Jest jeszcze jeden powód, żeby do kodu thinking wyłączać - czas. Te ukryte tokeny myślenia trzeba wygenerować, a to kosztuje.

Najlepiej widać to na gpt-oss. Surowa przepustowość wygląda na 54.5 tokena na sekundę - przyzwoicie. Ale widoczny output to tylko 15.1 tok/s, bo około 72% generacji to myślenie, którego nie widzisz w odpowiedzi. Na north różnica trybów jest jeszcze bardziej dosłowna: z thinkingiem ON 28.7 tok/s, z OFF 64.7 - ponad dwa razy szybciej za ten sam widoczny tekst.

Do kodu, gdzie thinking i tak szkodzi jakości, wyłączenie go jest podwójną wygraną: lepszy wynik i dwukrotnie szybciej.

## Wniosek: jeden przełącznik, dwie nastawy

Nie pytaj "czy włączyć thinking" jako globalnej decyzji o modelu. To źle postawione pytanie. Właściwa nastawa zależy od zadania:

- do kodu: thinking OFF - kod nie ginie w myśleniu, a generacja jest szybsza,
- do logiki: thinking ON - rozumowanie realnie podnosi trafność.

Najlepszym dowodem jest qwen3.6. Z thinkingiem wymuszonym na stałe wygląda albo na słabego kodera (4/8 z ON), albo na słabego logika (3.0 z OFF) - zależnie od tego, którą nastawę zamrozisz. A sterowany per zadanie (off do kodu, on do logiki) ląduje w czołówce OBU osi naraz. Ten sam model, dwa zadania, dwie odwrotne nastawy jednego przełącznika.

Lokalne modele nagradzają tych, którzy wiedzą, który przełącznik i kiedy ustawić. Thinking jest pierwszym z nich.

---

Configi modeli (`configs/`), zadania testowe (`prompts.json`), skrypty benchmarku (`bench_*.py`) i surowe wyniki (`RESULTS.md`) są w repo: github.com/justi/ollama-bench. Każdą liczbę z tego tekstu odpalisz i sprawdzisz sam.
