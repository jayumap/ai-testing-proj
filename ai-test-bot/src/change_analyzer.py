import subprocess
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
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
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
    return run_git_command(
        "diff",
        "--",
        str(source_file),
    )


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

        print("=" * 70)
        print(f"CHANGED SOURCE: {source_file}")
        print(f"TEST FILE:      {test_file}")
        print(f"TEST EXISTS:    {(REPO_ROOT / test_file).exists()}")
        print("=" * 70)

        print("\n--- GIT DIFF ---")
        print(get_file_diff(source_file))

        print("\n--- PRODUCTION SOURCE ---")
        print(read_file(source_file))

        if (REPO_ROOT / test_file).exists():
            print("\n--- EXISTING TEST SOURCE ---")
            print(read_file(test_file))


if __name__ == "__main__":
    main()