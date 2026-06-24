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
import ast
import json
import re
import signal
import sys
from contextlib import contextmanager

from _common import generate, load_prompts


class _Timeout(Exception):
    pass


@contextmanager
def _time_limit(seconds):
    """Twardy limit czasu na wykonanie (SIGALRM). Modele bywaja generuja kod z nieskonczona
    petla (while True bez wyjscia) - bez tego exec/wywolanie funkcji wisi w nieskonczonosc na
    100% CPU (realny przypadek: unsloth-q4xl zawiesil benchmark na 80+ min CPU). Dziala w
    glownym watku na Unix. Uwaga: kod z bare 'except:' moze zlapac _Timeout - dla zwyklej
    petli (bez except) SIGALRM przechodzi i jest lapany wyzej."""
    def handler(signum, frame):
        raise _Timeout()
    old = signal.signal(signal.SIGALRM, handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


def extract_code(text):
    """Wyciaga kod z odpowiedzi: preferuje fenced block z 'def', ktory parsuje sie do AST.

    Akceptuje dowolna etykiete jezyka (python/Python/python3/py...) case-insensitive
    i waliduje przez ast.parse, by nie exec'owac prozy (codex #8)."""
    blocks = re.findall(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", text, re.DOTALL)
    candidates = blocks if blocks else [text]
    for b in candidates:  # najpierw blok z 'def', ktory sie parsuje
        if "def " in b:
            try:
                ast.parse(b)
                return b
            except SyntaxError:
                continue
    for b in candidates:  # potem dowolny parsowalny
        try:
            ast.parse(b)
            return b
        except SyntaxError:
            continue
    return candidates[0]


def _norm(x):
    """Kanonizacja do porownania: krotki -> listy rekurencyjnie, by [(1,6)] == [[1,6]]
    (codex #4 - semantycznie poprawny wynik w innym ksztalcie nie ma falszywie oblewac)."""
    if isinstance(x, (list, tuple)):
        return [_norm(i) for i in x]
    return x


def run_generated(code, func_name, tests, timeout_s=5):
    """Exec kodu i sprawdzenie funkcji na przypadkach. Zwraca (ok, komunikat).

    Kazdy exec i kazde wywolanie funkcji ma twardy timeout (petla w kodzie modelu = oblany
    przypadek, nie zawieszenie benchmarku)."""
    ns = {}
    try:
        with _time_limit(timeout_s):
            exec(code, ns)
    except _Timeout:
        return False, f"timeout {timeout_s}s w exec (petla w kodzie modelu)"
    except Exception as e:
        return False, f"exec error: {type(e).__name__}: {e}"
    fn = ns.get(func_name)
    if not callable(fn):
        return False, f"brak funkcji {func_name}"
    for args, expected in tests:
        try:
            with _time_limit(timeout_s):
                got = fn(*args)
        except _Timeout:
            return False, f"timeout {timeout_s}s na {args} (petla w kodzie modelu)"
        except Exception as e:
            return False, f"runtime {type(e).__name__} na {args}"
        if _norm(got) != _norm(expected):
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
    args = sys.argv[1:]
    no_think = "--no-think" in args  # wylacza thinking u thinking-modeli (qwen3.6, deepseek-r1, north)
    hard = "--hard" in args  # trudne algorytmy LeetCode (sliding window, histogram, DP)
    expert = "--expert" in args  # nietrywialne, edge-case, scisla specyfikacja (rozroznia modele)
    # --think=VALUE: jawny poziom thinking. gpt-oss NIE da sie wylaczyc (harmony), tylko low|medium|high;
    # Qwen-distill: false dziala. Mapowanie: false->False, none/default->None, reszta (low/high)->string.
    think_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--think=")), None)
    if think_arg is not None:
        think = False if think_arg == "false" else (None if think_arg in ("none", "default") else think_arg)
    else:
        think = False if no_think else None
    # --num-predict=N: budzet tokenow generacji. Domyslnie 1500, ale gadatliwe modele (duzo
    # komentarzy) ucinaja sie na tym i kod nie parsuje (SyntaxError = false negative, NIE
    # slabosc modelu). Zmierzone: unsloth-q4xl done_reason=length przy 1500. Wyzszy budzet =
    # uczciwiej dla gadatliwych; modele konczace sie naturalnie (done=stop) nie zmieniaja wyniku.
    np_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--num-predict=")), None)
    gen_np = int(np_arg) if np_arg else 1500
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Uzycie: python3 bench_coding.py [--no-think] [--hard|--expert] [--num-predict=N] MODEL [...]")
        sys.exit(1)
    C = load_prompts()["coding"]
    gen_tasks = C["generate_expert"] if expert else (C["generate_hard"] if hard else C["generate"])
    bug_tasks = C["bugfind"]
    total = len(gen_tasks) + len(bug_tasks)

    results = {}
    for m in models:
        print(f"\n== {m} ==")
        gen_pass, details = 0, []
        print("  [generacja kodu - auto-test]")
        for t in gen_tasks:
            trunc = False
            try:
                r = generate(m, t["prompt"], num_predict=gen_np, think=think)
                # done_reason=='length' = odpowiedz ucieta budzetem (false negative ryzyko)
                trunc = r.get("done_reason") == "length"
                code = extract_code(r.get("response") or "")
                ok, msg = run_generated(code, t["func"], t["tests"])
            except Exception as e:
                ok, msg = False, f"blad: {e}"
            if not ok and trunc:
                msg = f"[UCIETE num_predict={gen_np}] {msg}"
            gen_pass += 1 if ok else 0
            flag = "OK " if ok else ("TR!" if trunc else "NIE")
            print(f"    {t['func']:<18} {flag}  {('' if ok else msg)[:60]}")
            details.append({"task": t["func"], "ok": ok, "trunc": trunc, "msg": msg})
        bug_pass = 0
        print("  [bug finding]")
        for i, t in enumerate(bug_tasks, 1):
            ans = ""
            try:
                r = generate(m, t["prompt"], num_predict=800, think=think)
                ans = r.get("response") or ""
                ok = grade_bug(ans, t["keys"])
            except Exception:
                ok = False
            bug_pass += 1 if ok else 0
            print(f"    bug {i:<14} {'OK ' if ok else 'NIE'}")
            # zapisujemy pelna odpowiedz - auto-grade bywa zawodny, audyt reczny po (codex #5)
            details.append({"task": f"bug{i}", "ok": ok, "answer": ans})
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
