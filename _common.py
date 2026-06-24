"""Wspolne funkcje: rozmowa z Ollama po HTTP, bez zewnetrznych zaleznosci."""
import json
import os
import time
import urllib.request

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

_PROMPTS = None


def load_prompts():
    """Wczytuje prompts.json z katalogu repo (cache w pamieci)."""
    global _PROMPTS
    if _PROMPTS is None:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "prompts.json"), encoding="utf-8") as f:
            _PROMPTS = json.load(f)
    return _PROMPTS


def list_loaded():
    """Modele aktualnie zaladowane w pamieci (GET /api/ps).

    Zwraca liste nazw, albo None gdy odczyt /api/ps SIE NIE POWIODL. Rozroznienie jest
    wazne: [] znaczy 'pamiec pusta', None znaczy 'nie wiadomo' - nie wolno mylic awarii
    kontroli izolacji z poprawna izolacja (codex finding #1)."""
    req = urllib.request.Request(OLLAMA_HOST + "/api/ps")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def unload(model):
    """Wyladowuje model z pamieci (keep_alive=0). Cicho ignoruje bledy."""
    try:
        generate(model, "", num_predict=0, keep_alive=0, timeout=60)
    except Exception:
        pass


def isolate(target, poll_timeout=30):
    """Wyladowuje wszystkie modele i CZEKA, az /api/ps potwierdzi pusta pamiec.
    Zwraca True gdy potwierdzono pustke, False przy bledzie odczytu lub timeout.
    Konkurencja o VRAM/RAM zanizа tok/s; bez tego pomiar jest niewiarygodny.

    Wazne (grok #3/#5): blad odczytu /api/ps (None) NIE konczy oczekiwania jako sukces -
    inaczej awaria API udawalaby oproniona pamiec. unload jest asynchroniczny, stad poll."""
    loaded = list_loaded()
    if loaded is None:
        return False  # nie udalo sie odczytac stanu - nie ruszamy na slepo
    for m in loaded:
        unload(m)
    waited = 0
    while waited < poll_timeout:
        cur = list_loaded()
        if cur is None:
            time.sleep(1)  # blad odczytu - probuj dalej, NIE traktuj jako pustka
            waited += 1
            continue
        if len(cur) == 0:
            return True
        time.sleep(1)
        waited += 1
    return False  # timeout - pamiec wciaz niepusta


def generate(model, prompt, num_predict=None, options=None, timeout=900, keep_alive=None, think=None):
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
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive
    if think is not None:
        payload["think"] = think  # Ollama: wylaczenie thinking u thinking-modeli (qwen3.6/gpt-oss)
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
