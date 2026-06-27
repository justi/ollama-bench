#!/usr/bin/env python3
"""Generate configs/*.best.Modelfile from models.json - params live in ONE place now.
Edit models.json, then run this; do NOT hand-edit the Modelfiles.

  python3 gen_modelfiles.py           # (re)write all Modelfiles from the manifest
  python3 gen_modelfiles.py --check   # verify on-disk Modelfiles match the manifest (param-equivalent,
                                      # order-independent); exit 1 on drift. Good as a pre-commit check.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, "models.json")))["models"]
ORDER = ["temperature", "top_k", "top_p", "min_p", "presence_penalty",
         "repeat_penalty", "num_ctx", "num_predict"]


def fmt(v):
    return str(v)


def render(name, cfg):
    p = cfg["params"]
    keys = [k for k in ORDER if k in p] + [k for k in p if k not in ORDER]
    lines = [
        f"# {name} - GENERATED from models.json. Do NOT hand-edit; edit models.json + run gen_modelfiles.py.",
        f"# {cfg.get('notes', '').strip()}",
        f"# ollama create {name} -f {cfg['modelfile']}",
        f"FROM {cfg['base']}",
    ]
    lines += [f"PARAMETER {k} {fmt(p[k])}" for k in keys]
    return "\n".join(lines) + "\n"


def param_lines(text):
    # FROM + sorted PARAMETER lines -> order-independent semantic identity
    fr = [l for l in text.splitlines() if l.startswith("FROM")]
    pa = sorted(l for l in text.splitlines() if l.startswith("PARAMETER"))
    return fr + pa


def main():
    check = "--check" in sys.argv
    drift = 0
    for name, cfg in M.items():
        path = os.path.join(HERE, cfg["modelfile"])
        new = render(name, cfg)
        if check:
            cur = open(path).read() if os.path.exists(path) else ""
            if param_lines(cur) != param_lines(new):
                drift = 1
                print(f"DRIFT {cfg['modelfile']}")
                print(f"  on-disk : {param_lines(cur)}")
                print(f"  manifest: {param_lines(new)}")
            else:
                print(f"ok   {cfg['modelfile']}")
        else:
            with open(path, "w") as f:
                f.write(new)
            print(f"wrote {cfg['modelfile']}")
    if check and drift:
        print("\n[!] DRIFT: on-disk Modelfiles differ from models.json - run gen_modelfiles.py")
    sys.exit(drift)


if __name__ == "__main__":
    main()
