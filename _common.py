"""Common functions: talking to Ollama over HTTP, without external dependencies."""
import json
import os
import time
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_PROMPTS = None


def load_prompts():
    """Loads the prompts file from the repo directory (cached in memory).

    Defaults to prompts_pl.json (the original Polish benchmark). Set the env var
    BENCH_PROMPTS to pick another file, e.g. BENCH_PROMPTS=prompts_en.json for the
    English variant - used by the PL-vs-EN language-effect comparison."""
    global _PROMPTS
    if _PROMPTS is None:
        here = os.path.dirname(os.path.abspath(__file__))
        fname = os.environ.get("BENCH_PROMPTS", "prompts_pl.json")
        with open(os.path.join(here, fname), encoding="utf-8") as f:
            _PROMPTS = json.load(f)
    return _PROMPTS


def list_loaded():
    """Models currently loaded in memory (GET /api/ps).

    Returns a list of names, or None when reading /api/ps FAILED. The distinction is
    important: [] means 'memory empty', None means 'unknown' - you must not confuse a failure
    of the isolation check with correct isolation (codex finding #1)."""
    req = urllib.request.Request(OLLAMA_HOST + "/api/ps")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def unload(model):
    """Unloads the model from memory (keep_alive=0). Silently ignores errors."""
    try:
        generate(model, "", num_predict=0, keep_alive=0, timeout=60)
    except Exception:
        pass


def isolate(target, poll_timeout=30):
    """Unloads all models and WAITS until /api/ps confirms empty memory.
    Returns True when emptiness is confirmed, False on a read error or timeout.
    Competition for VRAM/RAM lowers tok/s; without this the measurement is unreliable.

    Important (grok #3/#5): a /api/ps read error (None) does NOT end the wait as success -
    otherwise an API failure would masquerade as emptied memory. unload is asynchronous, hence the poll."""
    loaded = list_loaded()
    if loaded is None:
        return False  # failed to read state - we don't proceed blindly
    for m in loaded:
        unload(m)
    waited = 0
    while waited < poll_timeout:
        cur = list_loaded()
        if cur is None:
            time.sleep(1)  # read error - keep trying, do NOT treat as empty
            waited += 1
            continue
        if len(cur) == 0:
            return True
        time.sleep(1)
        waited += 1
    return False  # timeout - memory still not empty


def generate(model, prompt, num_predict=None, options=None, timeout=900, keep_alive=None, think=None):
    """Calls /api/generate (stream=false) and returns the full JSON response.

    Key fields in the Ollama response:
      - response          : generated text
      - eval_count        : number of generated tokens
      - eval_duration     : generation time in nanoseconds
      - prompt_eval_count : number of prompt tokens
      - prompt_eval_duration : prompt processing time (ns)
      - total_duration    : total time (ns)
    """
    opts = dict(options or {})
    if num_predict is not None:
        opts["num_predict"] = num_predict
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": opts,
    }
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    if think is not None:
        payload["think"] = think  # Ollama: disabling thinking on thinking-models (qwen3.6/gpt-oss)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_HOST + "/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    body["_wall_seconds"] = round(time.time() - t0, 2)
    return body


def gen_tok_s(resp):
    """generation tok/s from eval_count / eval_duration."""
    ec = resp.get("eval_count") or 0
    ed = resp.get("eval_duration") or 0
    if ec and ed:
        return round(ec / (ed / 1e9), 1)
    return None


def prompt_tok_s(resp):
    pc = resp.get("prompt_eval_count") or 0
    pd = resp.get("prompt_eval_duration") or 0
    if pc and pd:
        return round(pc / (pd / 1e9), 1)
    return None


def total_seconds(resp):
    td = resp.get("total_duration") or 0
    return round(td / 1e9, 2) if td else resp.get("_wall_seconds")


def word_count(resp):
    return len((resp.get("response") or "").split())
