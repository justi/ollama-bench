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

# (pytanie, lista akceptowanych kluczy) - czytane z prompts.json
PUZZLES = [(p["q"], p["keys"]) for p in load_prompts()["reasoning"]]


def grade(answer, keys):
    # Normalizuj: usun markdown (**bold**, #, `) i sklej whitespace, zeby klucz
    # zlapal odpowiedz typu "**4**\nDziewczyn: **3**". re.DOTALL bo '.' ma przejsc przez newline.
    a = re.sub(r"[*#`]", " ", answer.lower())
    a = re.sub(r"\s+", " ", a)
    for k in keys:
        if re.search(k.lower(), a, re.DOTALL):
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
