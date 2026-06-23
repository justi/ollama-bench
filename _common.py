"""Wspolne funkcje: rozmowa z Ollama po HTTP, bez zewnetrznych zaleznosci."""
import json
import os
import time
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def generate(model, prompt, num_predict=None, options=None, timeout=900):
    """Wywoluje /api/generate (stream=false) i zwraca pelny JSON odpowiedzi.

    Kluczowe pola w odpowiedzi Ollamy:
      - response          : wygenerowany tekst
      - eval_count        : liczba wygenerowanych tokenow
      - eval_duration     : czas generacji w nanosekundach
      - prompt_eval_count : liczba tokenow promptu
      - prompt_eval_duration : czas przetwarzania promptu (ns)
      - total_duration    : calkowity czas (ns)
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
    """tok/s generacji z eval_count / eval_duration."""
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
