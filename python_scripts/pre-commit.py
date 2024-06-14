import subprocess
import sys
from pathlib import Path

import git


def main():
    # this will be in project/.git/hooks
    # index in parents:  2   / 1  / 0
    project_path = Path(__file__).resolve().parents[2]
    repository = git.Repo(project_path)

    def is_existing_python_file(change):
        # b_blob is None if a file is deleted.
        # a_* and b_* refer to the last commit and current changes, respectively.
        # b_path should also be None in this case:
        # https://gitpython.readthedocs.io/en/stable/reference.html#git.diff.Diff
        # but:
        # https://github.com/gitpython-developers/GitPython/issues/749
        return (
            # new file or non-deleted file
            (
                (change.a_blob is not None and change.b_blob is None)
                or (change.a_blob is not None and change.b_blob is not None)
            )
            and Path(change.b_path).suffix == ".py"  # a python file
            and (project_path / change.b_path).exists()  # existing path
            and "test_files" not in str(project_path / change.b_path)  # not a fixture
        )

    modified_python_files = [
        str(project_path / change.b_path)
        for change in repository.index.diff("HEAD")
        if is_existing_python_file(change)
    ]

    # skip commits that are merge requests, denoted by a .git/MERGE_REQUEST file.
    if modified_python_files and not (project_path / ".git" / "MERGE_REQUEST").exists():
        files_string = " ".join(modified_python_files)
        if not subprocess.run(f"{sys.executable} -m black {files_string}").returncode:
            return subprocess.run(f"git add {files_string}").returncode
        else:
            print("black failed to reformat files.")
            return 1
    return 0


if __name__ == "__main__":
    exit(main())
