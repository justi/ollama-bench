# Nie ma najlepszego lokalnego LLM. Jest najlepszy do zadania.

phi4 to najgorszy koder w mojej stawce siedmiu lokalnych modeli: mediana 3 na 9 trudnych zadań. Ten sam phi4 to najlepszy logik w całej stawce: 5.33 na 6 zagadek. qwen36 jest dokładnie odwrotnie - czołówka kodu (6/9), dno logiki bez thinkingu (3.0/6). Dwa modele zamieniają się miejscami zależnie od osi.

To nie jest dziwactwo dwóch modeli. To główny wniosek z całego benchmarku na M1 Max: pytanie "jaki jest najlepszy lokalny LLM" jest źle postawione. Najpierw zadanie, potem model.

## Inwersja kod-logika

Ranking modeli zależy od tego, co mierzysz, do tego stopnia, że ten sam dobór zadań potrafi go całkowicie odwrócić.

Na trudnym kodzie czoło to qwen36, unsloth i gpt-oss (mediana 6/9), a phi4 zamyka stawkę (3/9). Na logice kolejność się wywraca: phi4 na szczycie (5.33), devstral i unsloth tuż za nim (5.0), a qwen36 - lider kodu - spada na sam dół. Gdybym opublikował tylko jedną z tych tabel, dostałbyś dwa sprzeczne "rankingi najlepszych modeli". Oba prawdziwe, każdy o czym innym.

## Ale jakość to nie wszystko - jest jeszcze rachunek

Nawet w obrębie jednej osi liczy się więcej niż sam wynik. Bo model trzeba uruchomić, a to kosztuje czas i prąd.

qwen-coder ma kod 5/9 - tylko o punkt niżej od remisowego szczytu. Ale jest najszybszy w stawce (61 tok/s) i najtańszy energetycznie (0.204 kWh na milion tokenów), i robi to stabilnie. Za jeden punkt kodu więcej top-tier płaci 20-50% więcej energii i czasu. Do codziennej pracy z kodem i dużego wolumenu to czyni qwen-coder najlepszym ogólnym wyborem, mimo że nie wygrywa żadnej pojedynczej osi jakości.

Na drugim biegunie jest devstral. Dobry logik (5.0), ale 9.8 tok/s i 1.276 kWh na milion - około sześć razy więcej energii niż qwen-coder za ten sam output. Jakość bywa droga, i ta cena jest mierzalna, nie teoretyczna.

## "Nowszy i większy" nie wygrywa automatycznie

Kuszące jest założenie, że nowsza generacja albo większy model po prostu jest lepszy. Benchmark mówi: nie.

qwen3.6 to model nowszy i większy (36B, ogólnego przeznaczenia) niż dedykowany qwen-coder (30B). Na kodzie koder go bije - bo to jego domena, a nie domena modelu ogólnego. Sprawdziłem też osobno modny wariant: unsloth w kwantyzacji Q4_K_XL, hyped na forach jako lepszy. Po uczciwym pomiarze DORÓWNUJE zwykłej wersji z Ollamy - ani lepszy, ani gorszy. Liczy się dopasowanie typu modelu do zadania, nie metryka "nowszy/większy/modniejszy".

## Rozmiar nie przekłada się na przepustowość

Różnice prędkości są ogromne i nie idą za rozmiarem modelu. Na górze qwen-coder (61 tok/s) i north (51), na dole phi4 (20) i devstral (9.8). Najszybszy jest ponad sześć razy szybszy od najwolniejszego za ten sam widoczny output - a przecież to 24-miliardowy devstral siedzi na dnie, podczas gdy 30-miliardowy qwen-coder prowadzi. Większy w parametrach nie znaczy wolniejszy ani szybszy; o przepustowości decyduje coś innego niż sama liczba parametrów. Przy wyborze modelu prędkość trzeba więc zmierzyć osobno, nie wyczytać z rozmiaru.

## Więc który wybrać

Zamiast jednego "najlepszego" - mapa decyzji zależna od tego, co robisz:

- Dużo kodu, zależy ci na przepustowości i prądzie: qwen-coder. Najszybszy, najtańszy, kod tylko o punkt od szczytu.
- Najwyższy PEWNY kod, gdy powtarzalność ważniejsza niż prędkość: qwen36 (6/9, stabilny).
- Czysta logika: phi4 albo devstral (najlepsze reasoningi) - ale licz się z wolniejszą i droższą generacją.
- Jeden model do wszystkiego: qwen36 ze sterowaniem thinkingiem per zadanie (thinking off do kodu daje 6/9, thinking on do logiki daje 5.0) ląduje w czołówce obu osi naraz.

## Wniosek

Nie istnieje "najlepszy lokalny LLM" - istnieje najlepszy do kodu, najlepszy do logiki, najszybszy, najtańszy, i one nie są tym samym modelem. Benchmark mierzy dokładnie tyle, ile potrafią jego zadania, a dobór zadania potrafi odwrócić wynik na drugą stronę.

Zanim zapytasz, który model pobrać, odpowiedz najpierw na inne pytanie: do czego. Reszta z tego wynika.
