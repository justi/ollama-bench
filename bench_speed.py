#!/usr/bin/env python3
"""Mierzy tok/s generacji per model.

Odtwarza liczby typu "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s".

  python3 bench_speed.py qwen3-coder:30b gpt-oss:20b gemma3:27b
  python3 bench_speed.py --big qwen3-coder:30b devstral:24b   # duzy prompt (~12k tokenow)
"""
import json
import statistics
import sys

from _common import generate, gen_tok_s, prompt_tok_s, total_seconds, load_prompts, isolate, list_loaded

P = load_prompts()
SMALL_PROMPT = P["speed_small"]


def build_big_prompt():
    # prefix + block*repeat + suffix -> ~12-15k tokenow (kontekst narzedziowy agenta)
    b = P["speed_big"]
    return b["prefix"] + (b["block"] * b["repeat"]) + b["suffix"]


RUNS = 3  # liczba pomiarow per model PO warmupie; raportujemy mediane


def _strip_latest(n):
    return n[:-7] if n.endswith(":latest") else n


def measure_model(model, prompt, num_predict, runs=RUNS, think=None):
    # Izolacja: wyladuj WSZYSTKIE inne modele, by w pamieci byl tylko mierzony.
    # Wiecej niz jeden model = konkurencja o VRAM/RAM = zanizone, niewiarygodne tok/s.
    iso_confirmed = isolate(model)  # True dopiero gdy /api/ps potwierdzi pustke
    # Warmup: jeden krotki przebieg, by zaladowac model i skompilowac kernele Metal.
    # Bez tego pierwszy pomiar bywa zanizony (cold start). Wynik warmupu odrzucamy.
    # gen tok/s liczymy z eval_duration, ktore NIE zawiera load_duration (load z dysku poza tok/s).
    try:
        generate(model, "Czesc", num_predict=8, think=think)
    except Exception:
        pass
    # Weryfikacja: po warmupie w pamieci ma byc DOKLADNIE mierzony model.
    # Normalizacja :latest (grok #4): /api/ps zwraca np. 'deepseek-fast:latest'.
    loaded = list_loaded()
    norm = None if loaded is None else [_strip_latest(x) for x in loaded]
    isolation_ok = bool(iso_confirmed) and norm == [_strip_latest(model)]
    rates, last, think_chars, resp_chars = [], None, 0, 0
    for _ in range(runs):
        last = generate(model, prompt, num_predict=num_predict, think=think)
        gr = gen_tok_s(last)
        if gr:
            rates.append(gr)
        # grok #1: u modeli 'thinking' (gpt-oss) tresc idzie w pole thinking, a eval_count
        # liczy tokeny MYSLENIA. gen_tok_s to wtedy przepustowosc kanalu thinking, nie outputu.
        think_chars = len(last.get("thinking") or "")
        resp_chars = len(last.get("response") or "")
    med = round(statistics.median(rates), 1) if rates else None
    # rozrzut = max-min surowych przebiegow (consistency): maly = stabilny, duzy = zmienny
    spread = round(max(rates) - min(rates), 1) if len(rates) >= 2 else None
    # response_tok_s_est: dla modeli thinking eval_count liczy tokeny myslenia, wiec surowy
    # tok/s zawyza przepustowosc WIDOCZNEGO outputu. Szacujemy output proporcjonalnie do
    # udzialu znakow response w calym wygenerowanym tekscie (grok #1, codex round2 #1).
    resp_est = med
    if med and think_chars > 0 and (resp_chars + think_chars) > 0:
        resp_est = round(med * resp_chars / (resp_chars + think_chars), 1)
    return {
        "model": model,
        "eval_tok_s": med,               # surowa przepustowosc generacji (z tokenami thinking)
        "response_tok_s_est": resp_est,  # szacowany WIDOCZNY output (dla thinking < eval_tok_s)
        "gen_tok_s": med,                # alias wsteczny (= eval_tok_s)
        "gen_tok_s_spread": spread,      # max-min przebiegow = miara consistency
        "gen_tok_s_runs": rates,
        "prompt_tok_s": prompt_tok_s(last) if last else None,
        "total_s": total_seconds(last) if last else None,
        "gen_tokens": last.get("eval_count") if last else None,
        "isolated": isolation_ok,
        "loaded_during": loaded,
        "is_thinking": think_chars > 0,
        "response_chars": resp_chars,
        "thinking_chars": think_chars,
    }


def main():
    args = sys.argv[1:]
    big = "--big" in args
    # --think=VALUE: jawny poziom (false->wylacz; low/high->string dla gpt-oss); inaczej --no-think
    think_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--think=")), None)
    if think_arg is not None:
        think = False if think_arg == "false" else (None if think_arg in ("none", "default") else think_arg)
    else:
        think = False if "--no-think" in args else None
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Uzycie: python3 bench_speed.py [--big] MODEL [MODEL ...]")
        sys.exit(1)

    prompt = build_big_prompt() if big else SMALL_PROMPT
    # --big: 256 (nie 64) tokenow generacji - przy 64 gen tok/s jest podatne na szum/EOS
    # po duzym promptcie (codex #3). Prompt-eval i tak mierzymy osobno przez prompt_tok_s.
    num_predict = 256 if big else 300
    mode = "DUZY PROMPT (~12k tok)" if big else "maly prompt"
    print(f"== bench_speed [{mode}] : warmup + mediana z {RUNS} przebiegow ==\n")

    rows = []
    for m in models:
        print(f"  {m} ... ", end="", flush=True)
        try:
            row = measure_model(m, prompt, num_predict, think=think)
        except Exception as e:
            print(f"BLAD: {e}")
            rows.append({"model": m, "error": str(e)})
            continue
        rows.append(row)
        warn = "" if row.get("isolated") else f"  [!] IZOLACJA NARUSZONA (w pamieci: {row.get('loaded_during')})"
        # UWAGA: osobna nazwa (think_note), NIE 'think' - nadpisanie parametru petli psulo
        # kolejne modele ("think":"" -> HTTP 400 u wszystkich po pierwszym).
        think_note = ""
        if row.get("is_thinking"):
            think_note = (f"  [!] THINKING: tok/s zawiera tokeny myslenia, nie tylko output "
                          f"(response {row['response_chars']} zn / thinking {row['thinking_chars']} zn)")
        print(f"gen {row['gen_tok_s']} tok/s (mediana z {row['gen_tok_s_runs']}) | "
              f"prompt {row['prompt_tok_s']} tok/s | total {row['total_s']} s{warn}{think_note}")

    print("\n== PODSUMOWANIE (mediana z 3, izolacja) ==")
    print(f"{'model':<30}{'output tok/s':>13}{'eval tok/s':>12}  uwaga")
    for r in rows:
        if "error" in r:
            print(f"{r['model']:<30}{'BLAD':>13}")
            continue
        # grok #1/#2 codex round2: brak izolacji = liczba niewiarygodna; thinking = eval > output
        if not r.get("isolated"):
            note = "[!] BRAK IZOLACJI - liczba niepewna"
        elif r.get("is_thinking"):
            note = "thinking: eval_tok_s zawiera myslenie, output nizszy"
        else:
            note = ""
        out = r.get("response_tok_s_est")
        ev = r.get("eval_tok_s")
        print(f"{r['model']:<30}{str(out):>13}{str(ev):>12}  {note}")

    with open("results_speed.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_speed.json")


if __name__ == "__main__":
    main()
