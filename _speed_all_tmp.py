import json
import statistics
from _common import generate, isolate, gen_tok_s

PROMPT = "Napisz funkcje Python is_prime(n) i krotko wyjasnij dzialanie."
MODELS = ["qwen-coder-t07", "gpt-oss-t07", "devstral-t07", "north-t07", "phi4-t07", "qwen36-t07"]
res = {}
for m in MODELS:
    isolate(m)
    try:
        generate(m, "Czesc", num_predict=8)
    except Exception:
        pass
    rates, last = [], None
    for _ in range(2):
        last = generate(m, PROMPT, num_predict=2000)
        gr = gen_tok_s(last)
        if gr:
            rates.append(gr)
    ev = round(statistics.median(rates), 1) if rates else None
    resp = len(last.get("response") or "")
    think = len(last.get("thinking") or "")
    out = round(ev * resp / (resp + think), 1) if ev and think > 0 and (resp + think) > 0 else ev
    res[m] = {"eval": ev, "output": out, "resp": resp, "think": think}
    print(f"{m}: output {out} | eval {ev} | think {think}zn", flush=True)
json.dump(res, open("results_speed_t07.json", "w"), indent=2)
print("SPEED DONE", flush=True)
