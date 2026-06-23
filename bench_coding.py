#!/usr/bin/env python3
"""Jakosc KODOWA: generacja funkcji (auto-test przez uruchomienie) + bug finding.

Domyka macierz jakosci o wymiar programistyczny - wazny, bo testowane modele to w
wiekszosci modele kodowe (qwen-coder, deepseek-coder, devstral). Reasoning (zagadki
logiczne) to inny wymiar; tu sprawdzamy realne pisanie i czytanie kodu.

  python3 bench_coding.py qwen3-coder:30b-fast deepseek-fast gpt-oss-fast devstral-small-2:24b-fast

OSTRZEZENIE BEZPIECZENSTWA: skrypt URUCHAMIA (exec) kod wygenerowany przez model na
lokalnych przypadkach testowych. Uruchamiaj tylko na zaufanych modelach lokalnych.
Kazda funkcja jest exec w osobnym namespace, ale to nadal wykonanie kodu z LLM.
"""
import json
import re
import sys

from _common import generate, load_prompts


def extract_code(text):
    """Wyciaga kod z odpowiedzi: preferuje blok ```python``` zawierajacy 'def'."""
    blocks = re.findall(r"```(?:python|py)?\s*(.*?)```", text, re.DOTALL)
    if blocks:
        for b in blocks:
            if "def " in b:
                return b
        return blocks[0]
    return text  # fallback: caly tekst (model mogl nie uzyc bloku)


def run_generated(code, func_name, tests):
    """Exec kodu i sprawdzenie funkcji na przypadkach. Zwraca (ok, komunikat)."""
    ns = {}
    try:
        exec(code, ns)
    except Exception as e:
        return False, f"exec error: {type(e).__name__}: {e}"
    fn = ns.get(func_name)
    if not callable(fn):
        return False, f"brak funkcji {func_name}"
    for args, expected in tests:
        try:
            got = fn(*args)
        except Exception as e:
            return False, f"runtime {type(e).__name__} na {args}"
        if got != expected:
            return False, f"{func_name}({args})={got!r}, oczek {expected!r}"
    return True, "OK"


def grade_bug(answer, keys):
    a = re.sub(r"[*#`]", " ", answer.lower())
    a = re.sub(r"\s+", " ", a)
    for k in keys:
        if re.search(k.lower(), a):
            return True
    return False


def main():
    models = sys.argv[1:]
    if not models:
        print("Uzycie: python3 bench_coding.py MODEL [MODEL ...]")
        sys.exit(1)
    C = load_prompts()["coding"]
    gen_tasks, bug_tasks = C["generate"], C["bugfind"]
    total = len(gen_tasks) + len(bug_tasks)

    results = {}
    for m in models:
        print(f"\n== {m} ==")
        gen_pass, details = 0, []
        print("  [generacja kodu - auto-test]")
        for t in gen_tasks:
            try:
                r = generate(m, t["prompt"], num_predict=1500)
                code = extract_code(r.get("response") or "")
                ok, msg = run_generated(code, t["func"], t["tests"])
            except Exception as e:
                ok, msg = False, f"blad: {e}"
            gen_pass += 1 if ok else 0
            print(f"    {t['func']:<18} {'OK ' if ok else 'NIE'}  {('' if ok else msg)[:60]}")
            details.append({"task": t["func"], "ok": ok, "msg": msg})
        bug_pass = 0
        print("  [bug finding]")
        for i, t in enumerate(bug_tasks, 1):
            try:
                r = generate(m, t["prompt"], num_predict=800)
                ok = grade_bug(r.get("response") or "", t["keys"])
            except Exception:
                ok = False
            bug_pass += 1 if ok else 0
            print(f"    bug {i:<14} {'OK ' if ok else 'NIE'}")
            details.append({"task": f"bug{i}", "ok": ok})
        score = gen_pass + bug_pass
        print(f"  SCORE: {score}/{total}  (kod {gen_pass}/{len(gen_tasks)}, bugi {bug_pass}/{len(bug_tasks)})")
        results[m] = {"score": score, "max": total, "gen": gen_pass, "bug": bug_pass, "details": details}

    print("\n== PODSUMOWANIE (jakosc kodowa) ==")
    for m, r in results.items():
        print(f"  {m:<30} {r['score']}/{r['max']}  (kod {r['gen']}/{len(gen_tasks)}, bugi {r['bug']}/{len(bug_tasks)})")

    with open("results_coding.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_coding.json")


if __name__ == "__main__":
    main()
