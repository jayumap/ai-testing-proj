import os
import subprocess

from change_analyzer import get_changed_files
from context_builder import get_contexts
from prompt_builder import build_messages
from llm_client import generate_test
from safe_writer import write_test_file
from git_safety import get_git_status, validate_generated_changes


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))


def run_maven_tests():
    print()
    print("[7/8] Running Maven validation...")

    if os.name == "nt":
        command = ["mvnw.cmd", "clean", "test"]
    else:
        command = ["./mvnw", "clean", "test"]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Maven validation failed. "
            "The generated test was not accepted."
        )

    print()
    print("  Maven validation passed.")
    print("  All project tests passed.")


def main():
    print("=" * 70)
    print("AI TEST AUTOMATION")
    print("=" * 70)
    print()

    print("[1/8] Capturing Git state before automation...")
    before_changes = get_git_status()

    for file in before_changes:
        print(f"  - {file}")

    print()
    print("[2/8] Detecting changed production files...")
    changed_files = get_changed_files()

    if not changed_files:
        print("No changed production Java files found.")
        return

    for file in changed_files:
        print(f"  - {file}")

    print()
    print("[3/8] Building context...")
    contexts = get_contexts()

    if not contexts:
        print("No test-generation contexts found.")
        return

    context = contexts[0]

    print(f"  Source: {context['source_file']}")
    print(f"  Test:   {context['test_file']}")

    print()
    print("[4/8] Building LLM prompt...")
    messages = build_messages(context)

    print("  Prompt built successfully.")

    print()
    print("[5/8] Generating test with LLM...")
    generated_test = generate_test(messages)

    print("  LLM generation successful.")
    print(f"  Generated characters: {len(generated_test)}")

    print()
    print("[6/8] Safely writing generated test...")
    test_path = write_test_file(
        context["test_file"],
        generated_test
    )

    print(f"  Test written to: {test_path}")

    run_maven_tests()

    print()
    print("[8/8] Validating Git changes...")

    after_changes = get_git_status()

    validate_generated_changes(
        before_changes,
        after_changes,
        context["test_file"]
    )

    print("  Git safety check passed.")
    print("  Only the expected test file was modified by automation.")

    print()
    print("=" * 70)
    print("PIPELINE COMPLETED SAFELY")
    print("=" * 70)


if __name__ == "__main__":
    main()