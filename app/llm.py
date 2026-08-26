"""Resume editing through a configured provider or the local Ollama model."""
import json
import os
from urllib import request

SYSTEM = """You are Unibot, a precise resume editor. Follow the user's instruction exactly.
Never invent employers, qualifications, technologies, metrics, or achievements.
Preserve facts, dates, names, and numbers unless the user explicitly changes them.
Return only the revised text with no introduction, quotes, markdown fence, or explanation."""

def _post(url: str, payload: dict, headers: dict | None = None, timeout: int = 120) -> dict:
    req = request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", **(headers or {})}, method="POST")
    with request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read())

def _complete(user_prompt: str) -> str:
    base, key, model = os.getenv("LLM_API_BASE"), os.getenv("LLM_API_KEY"), os.getenv("LLM_MODEL")
    if base and key and model:
        data = _post(base.rstrip("/") + "/chat/completions", {"model":model,"temperature":0.15,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":user_prompt}]}, {"Authorization":"Bearer "+key})
        return data["choices"][0]["message"]["content"].strip()
    data = _post("http://127.0.0.1:11434/api/chat", {"model":os.getenv("OLLAMA_MODEL","llama3:latest"),"stream":False,"options":{"temperature":0.15},"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":user_prompt}]})
    return data["message"]["content"].strip()

def rewrite(selected_text: str, instruction: str) -> str:
    try:
        return _complete(f"Instruction: {instruction}\n\nRewrite only this selected resume text:\n{selected_text}")
    except Exception as exc:
        raise RuntimeError(f"Local AI model is unavailable: {exc}") from exc

def edit_resume(raw_text: str, instruction: str) -> str:
    try:
        return _complete(f"Instruction: {instruction}\n\nEdit the correct section of this resume. Return the complete resume, preserving every unrelated line exactly:\n\n{raw_text}")
    except Exception as exc:
        raise RuntimeError(f"Local AI model is unavailable: {exc}") from exc
