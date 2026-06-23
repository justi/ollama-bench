#!/usr/bin/env python3
"""Pokazuje wplyw num_predict na dlugosc odpowiedzi i czas - dla modelu z trybem myslenia.

Odtwarza liczby: "domyslny limit ~293 slow -> num_predict 3000 ~747 slow, ~45 s -> ~85 s".

  python3 bench_numpredict.py gpt-oss:20b
  python3 bench_numpredict.py gpt-oss:20b 1500 3000   # wlasne progi
"""
import json
import sys

from _common import generate, total_seconds, word_count

# Zadanie wymagajace dluzszej odpowiedzi - model z myslenie najpierw "mysli",
# wiec przy niskim limicie ucina wlasciwa odpowiedz (thinking overflow).
TASK = (
    "Rozwaz odwrotny lancuch przyczynowo-skutkowy. Model jezykowy osiagnal slaby "
    "wynik AUC na zbiorze testowym. Wymien co najmniej dwie alternatywne sciezki "
    "przyczyn (od skutku do przyczyny), dla kazdego kroku zaznacz czy przyczyna jest "
    "konieczna czy wystarczajaca, i wskaz, ktora sciezka jest najbardziej prawdopodobna. "
    "Przedstaw to w formie tabeli z uzasadnieniem."
)


def main():
    if len(sys.argv) < 2:
        print("Uzycie: python3 bench_numpredict.py MODEL [low high]")
        sys.exit(1)
    model = sys.argv[2 - 1]
    low = int(sys.argv[3 - 1]) if len(sys.argv) > 2 else 1500
    high = int(sys.argv[4 - 1]) if len(sys.argv) > 3 else 3000

    print(f"== bench_numpredict [{model}] : num_predict {low} vs {high} ==\n")
    rows = []
    for np in (low, high):
        print(f"  num_predict={np} ... ", end="", flush=True)
        try:
            r = generate(model, TASK, num_predict=np)
        except Exception as e:
            print(f"BLAD: {e}")
            rows.append({"num_predict": np, "error": str(e)})
            continue
        wc = word_count(r)
        ts = total_seconds(r)
        rows.append({"num_predict": np, "words": wc, "total_s": ts, "gen_tokens": r.get("eval_count")})
        print(f"{wc} slow | {ts} s | {r.get('eval_count')} tokenow")

    print("\n== PODSUMOWANIE ==")
    print(f"{'num_predict':>12} {'slowa':>8} {'czas s':>8}")
    for r in rows:
        if "error" in r:
            print(f"{r['num_predict']:>12} {'BLAD':>8}")
        else:
            print(f"{r['num_predict']:>12} {r['words']:>8} {str(r['total_s']):>8}")
    if len(rows) == 2 and all("error" not in r for r in rows):
        dw = rows[1]["words"] - rows[0]["words"]
        print(f"\nWzrost dlugosci po podniesieniu limitu: +{dw} slow "
              f"({rows[0]['words']} -> {rows[1]['words']}).")

    with open("results_numpredict.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("Zapisano: results_numpredict.json")


if __name__ == "__main__":
    main()
