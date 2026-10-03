from context_builder import get_contexts
from prompt_builder import build_messages
from llm_client import generate_test


def main():
    contexts = get_contexts()

    if not contexts:
        print("No changed production Java files found.")
        return

    context = contexts[0]

    messages = build_messages(context)

    print("Sending context to LLM...")
    print()

    generated_test = generate_test(messages)

    print("=" * 70)
    print("GENERATED TEST FILE")
    print("=" * 70)
    print(generated_test)


if __name__ == "__main__":
    main()