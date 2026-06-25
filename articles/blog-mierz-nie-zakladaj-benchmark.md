# Jak benchmark cztery razy zmył własny ranking

Budowałem benchmark siedmiu lokalnych modeli LLM, żeby uczciwie porównać kod, logikę, szybkość i energię na M1 Max. Skrypty przeszły audyt dwóch niezależnych modeli - codex dwukrotnie plus grok, około trzydziestu uwag, wszystkie krytyczne naprawione. A potem ranking i tak odwracał się cztery razy. Ani razu przez model. Za każdym razem przez sposób pomiaru.

To jest historia o tym, że benchmark to nie tylko mierzony obiekt. To też narzędzie - i narzędzie trzeba audytować równie krytycznie jak to, co mierzy.

## Odwrócenie pierwsze: zła konfiguracja

qwen36 to najlepszy koder trudnych zadań w stawce - 6 na 9. Chyba że włączysz mu thinking. Wtedy spada na 0 na 9: ostatni, zero rozwiązanych zadań.

Problem nie był w modelu - był w jednym przełączniku. qwen36 z włączonym thinkingiem generuje tak długie rozumowanie, że zjada cały budżet tokenów, zanim dojdzie do kodu. Kod albo ląduje w ukrytym polu myślenia, albo jest ucinany w połowie - benchmark widzi pustkę, nie rozwiązanie (flaga ucięcia zapaliła się na niemal wszystkich z dziewięciu zadań). Po przełączeniu na `--no-think` ten sam model pisze kod od razu: 6/9, czoło stawki. To 0/9 nie mówiło nic o zdolności modelu. Mówiło o mojej konfiguracji.

Co ciekawe, rozmiar szkody zależy od tego, jak gadatliwie model myśli. north, który rozumuje oszczędnie, z thinkingiem i bez wypada prawie tak samo (4-5/9 vs 4/9). qwen36, który myśli rozwlekle, kolabuje z 6 do 0. Ta sama zła nastawa, dwa modele, zupełnie różny skutek.

## Odwrócenie drugie: ucięty budżet

unsloth dostał 3/9. Połowa jego porażek to były `SyntaxError` - kod, który się nie parsuje. Łatwo uznać model za niechlujny. Ale zamiast założyć, sprawdziłem, dlaczego kod jest niepoprawny - i odczytałem `done_reason` z odpowiedzi.

Okazało się, że odpowiedzi uderzały w sufit: `done_reason=length` i dokładnie 1500 tokenów. Jedno zadanie ucinało się w 2 na 3 próbach, inne w 1 na 3. unsloth jest bardzo gadatliwy (3500-6000 znaków z komentarzami), a benchmark miał zaszyty limit `num_predict=1500`. Kod był ucinany w połowie, więc się nie parsował. SyntaxError nie był słabością modelu - był artefaktem limitu.

Po podniesieniu budżetu do 3000 tokenów (i dodaniu detekcji ucięcia) unsloth dał 6/9. Dwa punkty różnicy z jednego parametru benchmarku. Lekcja: równy budżet dla wszystkich nie znaczy równa szansa - model gadatliwy traci więcej. Trzeba mierzyć `done_reason`, a nie zakładać, że limit nie wiąże.

## Odwrócenie trzecie: jeden przebieg to loteria

Mając poprawione configi, zmierzyłem ranking kodu raz - n=1. Wyglądał porządnie: qwen3.6 na czele, reszta za nim. Tylko że "raz" przy temperaturze 0.7 to za mało.

Puściłem każdy model trzy razy. phi4 dał kolejno: 2, 3, 5. gpt-oss: 6, 4, 7. Ten sam model, ten sam config, rozrzut trzech punktów na dziewięciu możliwych. Przy jednym przebiegu phi4 mógł trafić do tabeli jako "2/9, najgorszy" albo "5/9, środek" - czysty rzut monetą.

Mediana z trzech przebiegów pokazała, że ranking n=1 był błędny w 3 z 7 pozycji. Dopiero powtórzenie ujawniło, że szczyt kodu to remis trzech modeli, a nie jeden wyraźny lider. Pojedynczy pomiar zaszumionej wielkości nie jest wynikiem - jest jedną próbką z rozkładu.

## Odwrócenie czwarte: literówka w narzędziu

Przy pomiarze szybkości pierwszy model za każdym razem działał, a wszystkie kolejne zwracały HTTP 400 i napis BLAD. To nie był serwer ani modele.

To była kolizja nazw zmiennych w moim własnym skrypcie. Zmienna sterująca thinkingiem nazywała się `think`, a kilka linii niżej kod komunikatu ostrzegawczego nadpisywał ją pustym stringiem (`think = ""`). Po pierwszym modelu wszystkie kolejne dostawały więc `"think": ""` - niepoprawną wartość, którą serwer odrzucał czterechsetką. Pierwszy model przechodził, bo do niego zmienna była jeszcze poprawna.

Oznacza to, że wcześniejsze wielomodelowe pomiary szybkości - poza pierwszym modelem w każdym przebiegu - były niewiarygodne. Cicha literówka fałszowała liczby, a podsumowanie wyglądało wiarygodnie.

## Czego jeszcze nie biorę za fakt

Te cztery to nie wszystko. Energii w ogóle nie mierzyłem watomierzem - liczę ją ze zmierzonego tok/s i założonej stałej mocy 45 W, więc ranking energii jest pewny (wynika z prędkości), ale wartości bezwzględne to szacunek. Audyt złapał, że dla modeli z thinkingiem surowy tok/s liczy też tokeny myślenia - gpt-oss wyglądał na szybki przy 54 tok/s, choć jego widoczny output to 15. A automatyczny grader logiki odrzucał poprawne odpowiedzi, bo mylił "chłop" z "chlop" i nie rozumiał zapisu LaTeX ułamków.

## Meta-lekcja

Najmocniejsze w tym wszystkim jest to, że skrypty przeszły audyt dwóch modeli i około trzydziestu poprawek - i DALEJ miały te cztery błędy. Bo audyt patrzył na logikę kodu, a te bugi siedziały w styku narzędzia z mierzonymi modelami: w configu, w limicie tokenów, w liczbie prób, w nazwie zmiennej.

Wniosek jest niewygodny, ale trzeba go przyjąć: liczba z benchmarku bez audytu samego benchmarku to nie fakt. To hipoteza, która akurat wygląda jak fakt. Mierz - ale najpierw upewnij się, że mierzysz to, co myślisz, że mierzysz.

---

Skrypty benchmarku z opisanymi tu poprawkami (`bench_*.py`), configi modeli (`configs/`), zadania testowe (`prompts.json`) i pełne wyniki (`RESULTS.md`) są w repo: github.com/justi/ollama-bench. Bugi opisane wyżej i ich fixy są w historii commitów.
