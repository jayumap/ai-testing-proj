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


def parse_change_plan(content):
    content = content.strip()

    if not content:
        raise ValueError("LLM returned an empty response.")

    if content.startswith("```"):
        blocks = content.split("```")

        if len(blocks) >= 3:
            content = blocks[1].strip()

            if content.startswith("json"):
                content = content[4:].strip()

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"LLM response is not valid JSON: {error}"
        ) from error

    if not isinstance(plan, dict):
        raise ValueError(
            "LLM change plan must be a JSON object."
        )

    if "updates" not in plan:
        raise ValueError(
            "LLM change plan is missing 'updates'."
        )

    if "additions" not in plan:
        raise ValueError(
            "LLM change plan is missing 'additions'."
        )

    if not isinstance(plan["updates"], list):
        raise ValueError(
            "'updates' must be a JSON array."
        )

    if not isinstance(plan["additions"], list):
        raise ValueError(
            "'additions' must be a JSON array."
        )

    for update in plan["updates"]:
        if not isinstance(update, dict):
            raise ValueError(
                "Each update must be a JSON object."
            )

        if "test" not in update:
            raise ValueError(
                "Each update must contain 'test'."
            )

        if "replacement" not in update:
            raise ValueError(
                "Each update must contain 'replacement'."
            )

        if not isinstance(update["test"], str):
            raise ValueError(
                "Update 'test' must be a string."
            )

        if not isinstance(update["replacement"], str):
            raise ValueError(
                "Update 'replacement' must be a string."
            )

    for addition in plan["additions"]:
        if not isinstance(addition, dict):
            raise ValueError(
                "Each addition must be a JSON object."
            )

        if "name" not in addition:
            raise ValueError(
                "Each addition must contain 'name'."
            )

        if "code" not in addition:
            raise ValueError(
                "Each addition must contain 'code'."
            )

        if not isinstance(addition["name"], str):
            raise ValueError(
                "Addition 'name' must be a string."
            )

        if not isinstance(addition["code"], str):
            raise ValueError(
                "Addition 'code' must be a string."
            )

    return plan


def generate_test(messages):
    config = load_config()
    llm_config = config["llm"]
    provider = llm_config["provider"]

    if provider == "openrouter":
        return _generate_with_openrouter(
            llm_config=llm_config,
            messages=messages
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider}"
    )


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
    print(
        f"  Configured OpenRouter models: {len(models)}"
    )

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
            print(
                f"  Model temporarily unavailable: {error}"
            )
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

    return parse_change_plan(content)


if __name__ == "__main__":
    print("LLM client module loaded successfully.")
    print(f"Config path: {CONFIG_PATH}")