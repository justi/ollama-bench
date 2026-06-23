#!/usr/bin/env python3
"""6 zagadek logicznych z auto-grade po kluczu. Odtwarza score typu "gpt-oss 2/6, qwen 6/6".

  python3 bench_reasoning.py qwen3-coder:30b gpt-oss:20b

Auto-grade jest przyblizony (szuka klucza w odpowiedzi). Przy niejednoznacznych
odpowiedziach zajrzyj do results_reasoning.json i ocen recznie - to ten sam problem,
ktory w artykule rozwiazano ręczna ocena jakosci.
"""
import json
import re
import sys

from _common import generate

# (pytanie, lista akceptowanych kluczy - dopasowanie case-insensitive, dowolny z kluczy zalicza)
PUZZLES = [
    (
        "Marek ma tyle samo braci co siostr. Jego siostra Ania ma dwa razy wiecej braci "
        "niz siostr. Ilu jest chlopcow, a ile dziewczynek w rodzinie? Podaj same liczby.",
        [r"\b4\b.*\b3\b", r"czterech.*trzy", r"4 chlop", r"3 dziew"],
    ),
    (
        "Na wyspie sa rycerze (zawsze mowia prawde) i lotrzy (zawsze klamia). Spotykasz osobe "
        "A, ktora mowi: 'Jestem lotrem'. Kim jest A? Wyjasnij krotko.",
        [r"nie moze.*istnie", r"sprzeczn", r"paradoks", r"ani rycerz", r"niemozliw"],
    ),
    (
        "Masz problem przewozenia: wilk, koza i kapusta, lodka miesci ciebie i jeden przedmiot. "
        "Ile minimalnie przepraw przez rzeke potrzeba? Podaj liczbe.",
        [r"\b7\b", r"siedem"],
    ),
    (
        "Monty Hall: sa 3 bramki, za jedna auto. Wybierasz bramke 1. Prowadzacy otwiera bramke 3 "
        "(pusta). Czy oplaca sie zmienic wybor na bramke 2? Podaj decyzje i prawdopodobienstwo.",
        [r"zmieni", r"2/3", r"66", r"tak.*zmie"],
    ),
    (
        "Liczba 76 to kod ASCII ktorej wielkiej litery alfabetu lacinskiego? Podaj sama litere.",
        [r"\bL\b"],
    ),
    (
        "Slowo HELLO odwroc, wez trzecia litere wyniku. Jaka to litera? Podaj sama litere.",
        [r"\bL\b"],
    ),
]


def grade(answer, keys):
    a = answer.lower()
    for k in keys:
        if re.search(k.lower(), a):
            return True
    return False


def main():
    models = sys.argv[1:]
    if not models:
        print("Uzycie: python3 bench_reasoning.py MODEL [MODEL ...]")
        sys.exit(1)

    all_results = {}
    for m in models:
        print(f"\n== {m} ==")
        score = 0
        details = []
        for i, (q, keys) in enumerate(PUZZLES, 1):
            try:
                r = generate(m, q, num_predict=3000)
                ans = r.get("response") or ""
            except Exception as e:
                print(f"  Z{i}: BLAD {e}")
                details.append({"q": i, "error": str(e)})
                continue
            ok = grade(ans, keys)
            score += 1 if ok else 0
            print(f"  Z{i}: {'OK ' if ok else 'NIE'}  (dl. odp: {len(ans.split())} slow)")
            details.append({"q": i, "ok": ok, "answer": ans})
        print(f"  SCORE: {score}/{len(PUZZLES)}")
        all_results[m] = {"score": score, "max": len(PUZZLES), "details": details}

    print("\n== PODSUMOWANIE ==")
    for m, r in all_results.items():
        print(f"  {m:<32} {r['score']}/{r['max']}")

    with open("results_reasoning.json", "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_reasoning.json (zajrzyj tam, by ocenic niejednoznaczne recznie)")


if __name__ == "__main__":
    main()
