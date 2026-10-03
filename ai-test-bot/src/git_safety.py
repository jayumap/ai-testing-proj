import subprocess
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

TEST_ROOT = (REPO_ROOT / "src" / "test" / "java").resolve()


def get_git_status():
    """
    Return Git working-tree changes as a list of paths.

    Uses porcelain output so the result is stable and
    machine-readable.
    """

    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True
    )

    changes = []

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        # Porcelain format:
        # XY path
        path = line[3:]

        # Handle renamed files:
        # XY old -> new
        if " -> " in path:
            path = path.split(" -> ", 1)[1]

        changes.append(path)

    return changes


def validate_generated_changes(before_changes, after_changes, expected_test_file):
    before = set(before_changes)
    after = set(after_changes)

    expected = Path(expected_test_file).as_posix()

    after_normalized = {
        Path(path).as_posix()
        for path in after
    }

    if expected not in after_normalized:
        raise RuntimeError(
            "Expected generated test file was not detected after automation: "
            f"{expected}"
        )

    introduced = after - before

    introduced_normalized = {
        Path(path).as_posix()
        for path in introduced
    }

    unexpected = introduced_normalized - {expected}

    if unexpected:
        raise RuntimeError(
            "Git safety check failed. Unexpected files were modified by automation:\n"
            + "\n".join(sorted(unexpected))
        )

    return True


if __name__ == "__main__":
    print("Git safety module loaded successfully.")
    print(f"Repository root: {REPO_ROOT}")