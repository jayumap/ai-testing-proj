from change_analyzer import get_changed_files
from context_builder import get_contexts
from prompt_builder import build_messages
from llm_client import generate_test
from safe_writer import write_test_file


def main():
    print("=" * 70)
    print("AI TEST AUTOMATION")
    print("=" * 70)
    print()

    print("[1/5] Detecting changed production files...")
    changed_files = get_changed_files()

    if not changed_files:
        print("No changed production Java files found.")
        return

    for file in changed_files:
        print(f"  - {file}")

    print()
    print("[2/5] Building context...")
    contexts = get_contexts()

    if not contexts:
        print("No test-generation contexts found.")
        return

    context = contexts[0]

    print(f"  Source: {context['source_file']}")
    print(f"  Test:   {context['test_file']}")

    print()
    print("[3/5] Building LLM prompt...")
    messages = build_messages(context)

    print("  Prompt built successfully.")

    print()
    print("[4/5] Generating test with LLM...")
    generated_test = generate_test(messages)

    print("  LLM generation successful.")
    print(f"  Generated characters: {len(generated_test)}")

    print()
    print("[5/5] Safely writing generated test...")
    test_path = write_test_file(
        context["test_file"],
        generated_test
    )

    print(f"  Test written to: {test_path}")

    print()
    print("=" * 70)
    print("PIPELINE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()