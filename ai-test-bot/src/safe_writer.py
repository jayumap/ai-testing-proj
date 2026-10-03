from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

TEST_ROOT = (REPO_ROOT / "src" / "test" / "java").resolve()


def validate_test_path(test_file):
    """
    Ensure the framework-approved test path is safely located
    inside src/test/java and ends with Test.java.
    """

    test_path = (REPO_ROOT / test_file).resolve()

    # Prevent path traversal / escaping the test directory
    try:
        test_path.relative_to(TEST_ROOT)
    except ValueError:
        raise ValueError(
            f"Unsafe test path: {test_file}. "
            f"Path must remain inside {TEST_ROOT}"
        )

    # Only allow Java test files following the Test.java convention
    if test_path.suffix != ".java":
        raise ValueError(
            f"Unsafe test file: {test_file}. "
            "Only .java files are allowed."
        )

    if not test_path.name.endswith("Test.java"):
        raise ValueError(
            f"Unsafe test file: {test_file}. "
            "Test file must end with 'Test.java'."
        )

    return test_path


def validate_generated_content(generated_test):
    """
    Perform basic validation of the LLM-generated content.
    """

    if not generated_test or not generated_test.strip():
        raise ValueError("Generated test content is empty.")

    content = generated_test.strip()

    # The LLM was instructed not to return Markdown.
    if content.startswith("```") or content.endswith("```"):
        raise ValueError(
            "Generated test contains Markdown code fences."
        )

    # Basic Java sanity checks.
    if "class " not in content:
        raise ValueError(
            "Generated output does not appear to contain a Java class."
        )

    if "package " not in content:
        raise ValueError(
            "Generated output does not contain a Java package declaration."
        )

    return content


def write_test_file(test_file, generated_test):
    """
    Safely write generated test content to the framework-approved
    test file.
    """

    test_path = validate_test_path(test_file)
    content = validate_generated_content(generated_test)

    test_path.parent.mkdir(parents=True, exist_ok=True)

    test_path.write_text(
        content + "\n",
        encoding="utf-8"
    )

    return test_path


if __name__ == "__main__":
    print("Safe writer module loaded successfully.")
    print(f"Repository root: {REPO_ROOT}")
    print(f"Allowed test root: {TEST_ROOT}")