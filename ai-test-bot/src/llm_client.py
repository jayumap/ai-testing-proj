import json
import os
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
BOT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = BOT_ROOT / "config" / "config.json"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def generate_test(messages):
    config = load_config()
    llm_config = config["llm"]

    provider = llm_config["provider"]

    if provider == "openrouter":
        return _call_openrouter(
            llm_config=llm_config,
            messages=messages,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )


def _call_openrouter(llm_config, messages):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not set."
        )

    url = f"{llm_config['base_url'].rstrip('/')}/chat/completions"

    payload = {
        "model": llm_config["model"],
        "messages": messages,
        "temperature": llm_config.get("temperature", 0.1),
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180,
    )

    if not response.ok:
        raise RuntimeError(
            f"LLM API request failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    return data["choices"][0]["message"]["content"]