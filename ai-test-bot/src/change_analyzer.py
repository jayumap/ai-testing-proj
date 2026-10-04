import re
import subprocess
import os
from pathlib import Path


# Resolve the repository root from this script's location.
# This means the script does not depend on where you run it from.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# Repository-relative paths
SOURCE_ROOT = Path("src/main/java")
TEST_ROOT = Path("src/test/java")


def run_git_command(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


def get_changed_files():
    ci_base_sha = os.getenv("AI_TEST_BASE_SHA")

    if ci_base_sha:
        command = [
            "git",
            "diff",
            "--name-only",
            f"{ci_base_sha}...HEAD"
        ]
    else:
        command = [
            "git",
            "diff",
            "--name-only",
            "HEAD"
        ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True
    )

    changed_files = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        path = Path(line.strip())
        normalized = path.as_posix()

        if (
            normalized.startswith("src/main/java/")
            and path.suffix == ".java"
        ):
            changed_files.append(path)

    return changed_files


def find_test_file(source_file):
    relative_path = source_file.relative_to(SOURCE_ROOT)

    return (
        TEST_ROOT
        / relative_path.parent
        / f"{relative_path.stem}Test.java"
    )


def read_file(path):
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def get_file_diff(source_file):
    ci_base_sha = os.getenv("AI_TEST_BASE_SHA")

    if ci_base_sha:
        return run_git_command(
            "diff",
            f"{ci_base_sha}...HEAD",
            "--",
            str(source_file),
        )

    return run_git_command(
        "diff",
        "HEAD",
        "--",
        str(source_file),
    )


def extract_production_methods(source_source):
    """
    Extract production method declarations from Java source.

    This intentionally focuses on method declarations rather than
    trying to fully parse Java.
    """

    pattern = re.compile(
        r"(?:public|protected|private)\s+"
        r"(?:static\s+)?"
        r"(?:final\s+)?"
        r"[\w<>\[\], ?]+\s+"
        r"(\w+)\s*\([^;{}]*\)\s*\{",
        re.MULTILINE
    )

    methods = []

    for match in pattern.finditer(source_source):
        start_position = match.start()
        start_line = source_source.count(
            "\n",
            0,
            start_position
        ) + 1

        methods.append({
            "name": match.group(1),
            "start_line": start_line,
        })

    # Determine each method's ending line from the next method.
    for index, method in enumerate(methods):
        if index + 1 < len(methods):
            method["end_line"] = (
                methods[index + 1]["start_line"] - 1
            )
        else:
            method["end_line"] = (
                source_source.count("\n") + 1
            )

    return methods


def get_changed_line_ranges(diff):
    """
    Extract new-file line ranges from Git diff hunks.

    Example:
        @@ -20,3 +20,4 @@

    means lines 20-22 from the new file are represented
    by this hunk.
    """

    ranges = []

    for line in diff.splitlines():
        if not line.startswith("@@"):
            continue

        match = re.search(
            r"\+(\d+)(?:,(\d+))?",
            line
        )

        if not match:
            continue

        start = int(match.group(1))
        count = int(match.group(2) or "1")

        if count == 0:
            # A pure deletion does not introduce a new line.
            # The surrounding hunk still gives us the nearby
            # production method context.
            ranges.append((start, start))
            continue

        end = start + count - 1

        ranges.append((start, end))

    return ranges


def find_changed_methods(source_file):
    """
    Determine which current production methods overlap with
    changed Git diff hunks.
    """

    production_source = read_file(source_file)
    diff = get_file_diff(source_file)

    methods = extract_production_methods(
        production_source
    )

    changed_ranges = get_changed_line_ranges(diff)

    changed_methods = []

    for method in methods:
        for changed_start, changed_end in changed_ranges:

            overlaps = (
                method["start_line"] <= changed_end
                and method["end_line"] >= changed_start
            )

            if overlaps:
                changed_methods.append(method)
                break

    return changed_methods


def extract_test_methods(test_source):
    """
    Extract JUnit test methods and their bodies.

    Returns:
        [
            {
                "name": "...",
                "body": "..."
            }
        ]
    """

    pattern = re.compile(
        r"@Test\s+"
        r"(?:@[^\n]+\s+)*"
        r"(?:public\s+|private\s+|protected\s+)?"
        r"(?:static\s+)?"
        r"void\s+(\w+)\s*\([^)]*\)\s*\{",
        re.MULTILINE
    )

    tests = []

    for match in pattern.finditer(test_source):
        method_name = match.group(1)
        body_start = match.end()

        brace_count = 1
        position = body_start

        while position < len(test_source) and brace_count > 0:
            if test_source[position] == "{":
                brace_count += 1
            elif test_source[position] == "}":
                brace_count -= 1

            position += 1

        body = test_source[
            body_start:position - 1
        ]

        tests.append({
            "name": method_name,
            "body": body.strip(),
        })

    return tests


def map_tests_to_production_methods(
    test_source,
    production_source
):
    """
    Map each test method to the production methods it calls.
    """

    test_methods = extract_test_methods(test_source)
    production_methods = extract_production_methods(
        production_source
    )

    mapping = {
        method["name"]: []
        for method in production_methods
    }

    for test in test_methods:
        for production_method in production_methods:
            call_pattern = (
                rf"\b{re.escape(production_method['name'])}\s*\("
            )

            if re.search(
                call_pattern,
                test["body"]
            ):
                mapping[
                    production_method["name"]
                ].append(test["name"])

    return mapping


def get_affected_tests(source_file, test_file):
    """
    Return the existing tests affected by changed production
    methods.
    """

    if not (REPO_ROOT / test_file).exists():
        return {}

    production_source = read_file(source_file)
    test_source = read_file(test_file)

    changed_methods = find_changed_methods(
        source_file
    )

    mapping = map_tests_to_production_methods(
        test_source,
        production_source
    )

    affected = {}

    for method in changed_methods:
        affected[method["name"]] = mapping.get(
            method["name"],
            []
        )

    return affected


def main():
    changed_files = get_changed_files()

    java_sources = [
        file
        for file in changed_files
        if file.suffix == ".java"
        and file.is_relative_to(SOURCE_ROOT)
    ]

    if not java_sources:
        print("No changed production Java files found.")
        return

    for source_file in java_sources:
        test_file = find_test_file(source_file)

        changed_methods = find_changed_methods(
            source_file
        )

        print("=" * 70)
        print(f"CHANGED SOURCE: {source_file}")
        print(f"TEST FILE:      {test_file}")
        print(
            f"TEST EXISTS:    "
            f"{(REPO_ROOT / test_file).exists()}"
        )
        print("=" * 70)

        print("\n--- CHANGED METHODS ---")

        if not changed_methods:
            print("No changed production methods detected.")
        else:
            for method in changed_methods:
                print(
                    f"  - {method['name']} "
                    f"(lines "
                    f"{method['start_line']}-"
                    f"{method['end_line']})"
                )

        if (REPO_ROOT / test_file).exists():
            affected_tests = get_affected_tests(
                source_file,
                test_file
            )

            print("\n--- AFFECTED TESTS ---")

            if not affected_tests:
                print("No affected tests found.")
            else:
                for method, tests in affected_tests.items():
                    print()
                    print(
                        f"  PRODUCTION METHOD: {method}"
                    )

                    if not tests:
                        print("    No tests found.")
                    else:
                        for test in tests:
                            print(
                                f"    - {test}"
                            )

        print("\n--- GIT DIFF ---")
        print(get_file_diff(source_file))

        print("\n--- PRODUCTION SOURCE ---")
        print(read_file(source_file))

        if (REPO_ROOT / test_file).exists():
            print("\n--- EXISTING TEST SOURCE ---")
            print(read_file(test_file))


if __name__ == "__main__":
    main()