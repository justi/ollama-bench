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

from _common import generate, load_prompts

# (pytanie, keys-OR, anti-ODRZUC, all-grupy-AND) - czytane z prompts.json
PUZZLES = [(p["q"], p.get("keys", []), p.get("anti"), p.get("all")) for p in load_prompts()["reasoning"]]


def grade(answer, keys, anti=None, all_groups=None):
    # Normalizuj: usun markdown (**bold**, #, `) i sklej whitespace, zeby klucz
    # zlapal odpowiedz typu "**4**\nDziewczyn: **3**". re.DOTALL bo '.' ma przejsc przez newline.
    a = answer.lower()
    # LaTeX: \frac{2}{3} -> 2/3, usun \boxed \text \[ ] i nawiasy klamrowe (r1 pisze matematyke
    # w LaTeX, klucz "2/3" nie lapal "\frac{2}{3}" - false-negative, audyt reczny r1).
    a = re.sub(r"\\frac\s*\{(\d+)\}\s*\{(\d+)\}", r"\1/\2", a)
    a = re.sub(r"\\[a-z]+", " ", a)  # \boxed \text \frac itd.
    a = re.sub(r"[{}\\\[\]]", " ", a)
    # Diakrytyka -> ASCII, by klucz "chlop" lapal "chlopcow" pisane z polskimi znakami (ch-l-o-p
    # z 'l' kreskowanym). Audyt reczny r1: "4 chlopce" z 'l-kreska' nie lapalo klucza "4 chlop".
    a = a.translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
    a = re.sub(r"[*#`]", " ", a)
    a = re.sub(r"\s+", " ", a)
    # anti: jesli odpowiedz zawiera wzorzec sprzeczny/blędny, odrzuc (Monty Hall "rowne prawdopodob").
    if anti:
        for k in anti:
            if re.search(k.lower(), a, re.DOTALL):
                return False
    # all: KAZDA grupa musi miec >=1 trafienie (AND miedzy grupami). Z1 wymaga 4 chlop ORAZ 3 dziew,
    # inaczej "4 chlopcow, 100 dziewczynek" przeszloby (grok/codex round2 #4).
    if all_groups:
        for group in all_groups:
            if not any(re.search(k.lower(), a, re.DOTALL) for k in group):
                return False
        return True
    for k in keys:
        if re.search(k.lower(), a, re.DOTALL):
            return True
    return False


def main():
    args = sys.argv[1:]
    # --runs N: N pelnych przebiegow, raportuj SREDNIA + zakres. Tlumi szum temp 0.7 (+-1)
    # i ujawnia wariancje (model stabilny vs chaotyczny). Domyslnie 1.
    runs = 1
    if "--runs" in args:
        idx = args.index("--runs")
        try:
            runs = int(args[idx + 1])
        except (IndexError, ValueError):
            print("--runs wymaga liczby")
            sys.exit(1)
        args = args[:idx] + args[idx + 2:]
    no_think = "--no-think" in args  # wylacza thinking u thinking-modeli
    think = False if no_think else None
    models = [a for a in args if a != "--no-think"]
    if not models:
        print("Uzycie: python3 bench_reasoning.py [--runs N] [--no-think] MODEL [MODEL ...]")
        sys.exit(1)
    maxs = len(PUZZLES)

    all_results = {}
    for m in models:
        print(f"\n== {m} ==")
        run_scores, last_details = [], []
        for run_i in range(runs):
            score, details = 0, []
            for i, (q, keys, anti, all_g) in enumerate(PUZZLES, 1):
                try:
                    r = generate(m, q, num_predict=3000, think=think)
                    ans = r.get("response") or ""
                except Exception as e:
                    details.append({"q": i, "error": str(e)})
                    continue
                ok = grade(ans, keys, anti, all_g)
                score += 1 if ok else 0
                details.append({"q": i, "ok": ok, "answer": ans})
            run_scores.append(score)
            last_details = details
            print(f"  przebieg {run_i + 1}: {score}/{maxs}")
        mean = sum(run_scores) / len(run_scores)
        if runs > 1:
            print(f"  SREDNIA: {mean:.1f}/{maxs}  (zakres {min(run_scores)}-{max(run_scores)}, przebiegi {run_scores})")
        all_results[m] = {"mean": round(mean, 2), "runs": run_scores, "max": maxs, "details": last_details}

    print("\n== PODSUMOWANIE ==")
    for m, r in all_results.items():
        if len(r["runs"]) > 1:
            print(f"  {m:<30} srednia {r['mean']}/{r['max']}  zakres {min(r['runs'])}-{max(r['runs'])}  {r['runs']}")
        else:
            print(f"  {m:<30} {r['runs'][0]}/{r['max']}")

    with open("results_reasoning.json", "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_reasoning.json")


if __name__ == "__main__":
    main()
