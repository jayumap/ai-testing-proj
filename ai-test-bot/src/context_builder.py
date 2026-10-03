import json

from change_analyzer import (
    REPO_ROOT,
    SOURCE_ROOT,
    get_changed_files,
    find_test_file,
    read_file,
    get_file_diff,
)


TASK = "Generate or update unit tests for the changed production behavior."

RULES = [
    "Preserve all existing tests.",
    "Use JUnit 5.",
    "Follow the existing test file style.",
    "Add tests for the changed behavior.",
    "Do not modify production code.",
    "Do not modify pom.xml or CI configuration.",
    "Return the complete test file.",
]


def build_context(source_file):
    test_file = find_test_file(source_file)

    return {
        "project": {
            "language": "Java",
            "build_tool": "Maven",
            "test_framework": "JUnit 5",
        },
        "source_file": str(source_file),
        "test_file": str(test_file),
        "diff": get_file_diff(source_file),
        "production_source": read_file(source_file),
        "existing_tests": (
            read_file(test_file)
            if (REPO_ROOT / test_file).exists()
            else ""
        ),
        "task": TASK,
        "rules": RULES,
    }


def get_contexts():
    changed_files = get_changed_files()

    java_sources = [
        file
        for file in changed_files
        if file.suffix == ".java"
        and file.is_relative_to(SOURCE_ROOT)
    ]

    return [build_context(source_file) for source_file in java_sources]


def main():
    contexts = get_contexts()

    if not contexts:
        print("No changed production Java files found.")
        return

    for context in contexts:
        print("=" * 70)
        print("GENERATED CONTEXT")
        print("=" * 70)
        print(json.dumps(context, indent=2))


if __name__ == "__main__":
    main()
