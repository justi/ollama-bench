#!/usr/bin/env python3
"""Agent-style LONG-PROMPT timing: how long does a small code task take when the prompt
looks like an agentic editor's input (~12k tokens of system + tools + history)?

Measures, per model (1 discarded warmup + n=3, medians): total wall s, prompt tokens,
prompt eval tok/s, generation tok/s. Models isolated before each config.
Saved to agent_prompt_results.json (tracked; the blog offline-coding article cites it).
"""
import json
import statistics

from _common import generate, isolate

TOOLS = "\n".join(
    f"- narzedzie `{n}`: {d}. Parametry: path (string), zakres (int), dry_run (bool)."
    for n, d in [
        ("read_file", "czyta plik z dysku i zwraca tresc z numerami linii"),
        ("write_file", "zapisuje tresc do pliku, tworzy katalogi posrednie"),
        ("run_tests", "uruchamia zestaw testow i zwraca raport bledow"),
        ("grep_repo", "przeszukuje repozytorium wzorcem regex"),
        ("git_diff", "pokazuje niezacommitowane zmiany w formacie unified diff"),
        ("list_dir", "listuje pliki katalogu z rozmiarami i datami"),
    ])

HISTORY_TURN = (
    "Uzytkownik: popraw walidacje formularza w module rejestracji, bo puste pole przechodzi.\n"
    "Asystent: Sprawdzilam modul `registration/forms.py` narzedziem read_file. Walidacja pola "
    "email uzywa wyrazenia, ktore dopuszcza pusty ciag, bo kwantyfikator jest opcjonalny. "
    "Proponuje jawny warunek na niepusty ciag przed sprawdzeniem wzorca, do tego test "
    "jednostkowy na pusty input, spacje i poprawny adres. Po zapisie uruchomilam run_tests: "
    "raport czysty, 42 testy przechodza, pokrycie modulu wzroslo o dwa punkty procentowe.\n")

SYSTEM = ("Jestes asystentem kodowania w edytorze agentowym. Odpowiadasz po polsku, zwracasz "
          "kod w blokach markdown, uzywasz narzedzi gdy trzeba.\nDostepne narzedzia:\n" + TOOLS)

TASK = ("Napisz funkcje Pythona `merge_intervals(intervals)`: scala nachodzace przedzialy "
        "i zwraca posortowane po poczatku; stykajace sie jak [1,2] i [2,3] tez scala. "
        "Sam kod w jednym bloku, potem jedno zdanie o zlozonosci.")

MODELS = [("qwen-coder-best", False)]
RUNS = 3
NUM_CTX = 16384  # prompt ~12k tokens must FIT (model defaults truncate it)


def build_prompt():
    hist = HISTORY_TURN * 90  # ~12k tokens total with system+tools
    return SYSTEM + "\n\n[HISTORIA ROZMOWY]\n" + hist + "\n[NOWE ZADANIE]\n" + TASK


def main():
    prompt = build_prompt()
    print(f"prompt chars: {len(prompt)}")
    out = []
    for model, think in MODELS:
        isolate(model)
        print(f"\n== {model} (warmup + n={RUNS}) ==", flush=True)
        rows = []
        for i in range(RUNS + 1):
            # unique FIRST line per run busts ollama's prefix cache - each run pays
            # the full prompt eval (the agent-editor cold-prompt scenario)
            p = f"[sesja pomiarowa {i}]\n" + prompt
            r = generate(model, p, num_predict=600, think=think,
                         options={"num_ctx": NUM_CTX})
            pe_n = r.get("prompt_eval_count", 0)
            pe_s = r.get("prompt_eval_duration", 0) / 1e9
            ev_n = r.get("eval_count", 0)
            ev_s = r.get("eval_duration", 0) / 1e9
            tot = r.get("total_duration", 0) / 1e9
            row = {"total_s": round(tot, 1), "prompt_tokens": pe_n,
                   "prompt_tok_s": round(pe_n / pe_s, 1) if pe_s else None,
                   "gen_tok_s": round(ev_n / ev_s, 1) if ev_s else None}
            tag = "warmup(drop)" if i == 0 else f"run {i}/{RUNS}"
            print(f"  [{model}] {tag}: total {row['total_s']}s | prompt {pe_n} tok "
                  f"@ {row['prompt_tok_s']} tok/s | gen {row['gen_tok_s']} tok/s", flush=True)
            if i > 0:
                rows.append(row)
        med = {k: round(statistics.median(r[k] for r in rows), 1)
               for k in ("total_s", "prompt_tok_s", "gen_tok_s")}
        med["model"] = model
        med["prompt_tokens"] = rows[0]["prompt_tokens"]
        med["runs_total_s"] = [r["total_s"] for r in rows]
        out.append(med)
        print(f"  -> mediana: total {med['total_s']}s | gen {med['gen_tok_s']} tok/s", flush=True)
    with open("agent_prompt_results.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nSaved: agent_prompt_results.json", flush=True)


if __name__ == "__main__":
    main()
