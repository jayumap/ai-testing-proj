import json
import os
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "config.json"


class RetryableLLMError(Exception):
    pass


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def clean_generated_test(content):
    content = content.strip()

    if "```" in content:
        blocks = content.split("```")

        for block in blocks:
            block = block.strip()

            if block.startswith("java"):
                block = block[4:].strip()

            if (
                "package " in block
                and "class " in block
            ):
                return block.strip()

    package_index = content.find("package ")

    if package_index >= 0:
        content = content[package_index:]

    return content.strip()


def generate_test(messages):
    config = load_config()
    llm_config = config["llm"]
    provider = llm_config["provider"]

    if provider == "openrouter":
        return _generate_with_openrouter(
            llm_config=llm_config,
            messages=messages
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")


def _generate_with_openrouter(llm_config, messages):
    models = llm_config.get("models")

    if not models:
        single_model = llm_config.get("model")

        if not single_model:
            raise ValueError(
                "No LLM model configured. "
                "Add either 'model' or 'models' to config.json."
            )

        models = [single_model]

    if not isinstance(models, list) or not models:
        raise ValueError(
            "'models' must be a non-empty list."
        )

    failures = []

    print()
    print(f"  Configured OpenRouter models: {len(models)}")

    for index, model in enumerate(models, start=1):
        print()
        print(
            f"  Trying model {index}/{len(models)}: {model}"
        )

        try:
            result = _call_openrouter(
                llm_config=llm_config,
                model=model,
                messages=messages
            )

            print(f"  Model succeeded: {model}")

            return result

        except RetryableLLMError as error:
            print(f"  Model temporarily unavailable: {error}")
            print("  Trying next configured model...")

            failures.append(
                f"{model}: {error}"
            )

        except Exception as error:
            print(f"  Model failed: {error}")
            print("  Trying next configured model...")

            failures.append(
                f"{model}: {error}"
            )

    error_details = "\n".join(
        f"  - {failure}"
        for failure in failures
    )

    raise RuntimeError(
        "All configured LLM models failed.\n"
        + error_details
    )


def _call_openrouter(llm_config, model, messages):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not set."
        )

    base_url = llm_config.get(
        "base_url",
        "https://openrouter.ai/api/v1"
    )

    url = base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
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

    if response.status_code != 200:

        if response.status_code in {
            408,
            429,
            500,
            502,
            503,
            504,
        }:
            raise RetryableLLMError(
                f"HTTP {response.status_code}: {response.text}"
            )

        raise RuntimeError(
            f"LLM API request failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            f"Unexpected LLM response format: {data}"
        ) from error

    return clean_generated_test(content)


if __name__ == "__main__":
    print("LLM client module loaded successfully.")
    print(f"Config path: {CONFIG_PATH}")