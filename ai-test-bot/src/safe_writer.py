import re
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

    try:
        test_path.relative_to(TEST_ROOT)
    except ValueError:
        raise ValueError(
            f"Unsafe test path: {test_file}. "
            f"Path must remain inside {TEST_ROOT}"
        )

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


def read_test_file(test_file):
    test_path = validate_test_path(test_file)

    if not test_path.exists():
        raise FileNotFoundError(
            f"Test file does not exist: {test_file}"
        )

    return test_path.read_text(encoding="utf-8")


def extract_test_methods(test_source):
    """
    Extract JUnit @Test methods while preserving their
    exact source text and positions.
    """

    pattern = re.compile(
        r"(?P<method>"
        r"(?:(?:@[^\n]+\s*)+)"
        r"(?:public\s+|private\s+|protected\s+)?"
        r"(?:static\s+)?"
        r"void\s+"
        r"(?P<name>\w+)"
        r"\s*\([^)]*\)\s*\{"
        r")",
        re.MULTILINE
    )

    methods = []

    for match in pattern.finditer(test_source):
        method_start = match.start()
        body_start = match.end()

        brace_count = 1
        position = body_start

        while position < len(test_source) and brace_count > 0:
            if test_source[position] == "{":
                brace_count += 1
            elif test_source[position] == "}":
                brace_count -= 1

            position += 1

        if brace_count != 0:
            raise ValueError(
                f"Could not safely parse test method "
                f"'{match.group('name')}'."
            )

        methods.append(
            {
                "name": match.group("name"),
                "start": method_start,
                "end": position,
                "source": test_source[
                    method_start:position
                ],
            }
        )

    return methods


def validate_method_code(code, expected_name=None):
    """
    Validate that generated code contains exactly one test method
    and does not contain a class, package, import, or Markdown block.
    """

    if not isinstance(code, str) or not code.strip():
        raise ValueError(
            "Generated test method code is empty."
        )

    content = code.strip()

    if "```" in content:
        raise ValueError(
            "Generated test method contains Markdown code fences."
        )

    forbidden_tokens = [
        "package ",
        "import ",
        "class ",
        "interface ",
        "enum ",
    ]

    for token in forbidden_tokens:
        if token in content:
            raise ValueError(
                f"Generated test method contains forbidden "
                f"content: {token.strip()}"
            )

    methods = extract_test_methods(content)

    if len(methods) != 1:
        raise ValueError(
            "Generated code must contain exactly one @Test method."
        )

    method = methods[0]

    if expected_name and method["name"] != expected_name:
        raise ValueError(
            f"Generated method name '{method['name']}' "
            f"does not match expected name '{expected_name}'."
        )

    return content


def validate_change_plan(plan, existing_test_source):
    """
    Validate the LLM change plan before anything is written.
    """

    if not isinstance(plan, dict):
        raise ValueError(
            "Change plan must be a JSON object."
        )

    updates = plan.get("updates")
    additions = plan.get("additions")

    if not isinstance(updates, list):
        raise ValueError(
            "Change plan 'updates' must be a list."
        )

    if not isinstance(additions, list):
        raise ValueError(
            "Change plan 'additions' must be a list."
        )

    existing_methods = extract_test_methods(
        existing_test_source
    )

    existing_names = {
        method["name"]
        for method in existing_methods
    }

    update_names = set()

    for update in updates:
        if not isinstance(update, dict):
            raise ValueError(
                "Each update must be an object."
            )

        test_name = update.get("test")
        replacement = update.get("replacement")

        if not isinstance(test_name, str) or not test_name:
            raise ValueError(
                "Each update must contain a valid 'test' name."
            )

        if test_name not in existing_names:
            raise ValueError(
                f"Update targets non-existent test method: "
                f"{test_name}"
            )

        if test_name in update_names:
            raise ValueError(
                f"Duplicate update target: {test_name}"
            )

        update_names.add(test_name)

        validate_method_code(
            replacement,
            expected_name=test_name
        )

    addition_names = set()

    for addition in additions:
        if not isinstance(addition, dict):
            raise ValueError(
                "Each addition must be an object."
            )

        name = addition.get("name")
        code = addition.get("code")

        if not isinstance(name, str) or not name:
            raise ValueError(
                "Each addition must contain a valid 'name'."
            )

        if name in existing_names:
            raise ValueError(
                f"Addition duplicates existing test method: "
                f"{name}"
            )

        if name in addition_names:
            raise ValueError(
                f"Duplicate addition test method: {name}"
            )

        if name in update_names:
            raise ValueError(
                f"Test method cannot be both updated and added: "
                f"{name}"
            )

        addition_names.add(name)

        validate_method_code(
            code,
            expected_name=name
        )

    return True


def apply_change_plan(test_file, plan):
    """
    Apply only the approved test-method changes.

    Existing unrelated test methods and all other file content
    remain untouched.
    """

    test_path = validate_test_path(test_file)
    test_source = read_test_file(test_file)

    validate_change_plan(
        plan,
        test_source
    )

    updates = plan["updates"]
    additions = plan["additions"]

    methods = extract_test_methods(test_source)

    method_map = {
        method["name"]: method
        for method in methods
    }

    replacements = []

    for update in updates:
        method = method_map[update["test"]]

        replacement = validate_method_code(
            update["replacement"],
            expected_name=update["test"]
        )

        replacements.append(
            (
                method["start"],
                method["end"],
                replacement
            )
        )

    updated_source = test_source

    for start, end, replacement in sorted(
        replacements,
        reverse=True
    ):
        updated_source = (
            updated_source[:start]
            + replacement
            + updated_source[end:]
        )

    if additions:
        insertion = "\n\n" + "\n\n".join(
            validate_method_code(
                addition["code"],
                expected_name=addition["name"]
            )
            for addition in additions
        )

        class_end = updated_source.rfind("}")

        if class_end == -1:
            raise ValueError(
                "Could not find the end of the test class."
            )

        updated_source = (
            updated_source[:class_end]
            + insertion
            + "\n"
            + updated_source[class_end:]
        )

    if updated_source != test_source:
        test_path.write_text(
            updated_source,
            encoding="utf-8"
        )

    return test_path


if __name__ == "__main__":
    print("Safe writer module loaded successfully.")
    print(f"Repository root: {REPO_ROOT}")
    print(f"Allowed test root: {TEST_ROOT}")