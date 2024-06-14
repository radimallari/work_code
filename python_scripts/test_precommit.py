import os
import shutil
import filecmp
import subprocess
from tool_tests.fixtures.repository import repository
from pathlib import Path


test_fixtures = Path(__file__).resolve().parent / "fixtures"
test_files = test_fixtures / "test_files"

repo_path = test_fixtures / "cloned_repo"

unformatted_file = test_files / "unformatted.py"
text_file = test_files / "non_python_file.txt"


def git_commit(file_name, message, amend=False):
    """helper func to stage and commit files"""
    option = ""
    if amend is True:
        option = "--amend"

    subprocess.run(f"git add {file_name}", cwd=repo_path)
    subprocess.run(f'git commit {option} -m "{message}"', cwd=repo_path)


def test_existing_file(repository):
    """for reformatting pre-existing files"""
    formatted_file = test_files / "formatted2.py"
    # add file and commit to the repository
    shutil.copy(unformatted_file, repo_path)
    git_commit(unformatted_file.name, "initial test commit")

    # edit python file
    with open(repo_path / "unformatted.py", "a") as f:
        f.write("ugly_list_2 = ['hey' \n\n,\n'im a list', \n\t\t\n2]")

    # commit changes to the file
    git_commit((repo_path / "unformatted.py").name, "add text and reformat")

    assert filecmp.cmp(repo_path / "unformatted.py", formatted_file) is True


def test_new_file(repository):
    """for reformatting new files"""
    formatted_file = test_files / "formatted.py"

    # add file and commit to repository
    shutil.copy(unformatted_file, repo_path)

    # commit the file
    git_commit(unformatted_file.name, "initial test commit")

    # test if the file has been formatted
    assert filecmp.cmp(repo_path / "unformatted.py", formatted_file) is True


def test_deleted_file(repository):
    """for checking filenotfound errors"""
    # add file and commit to the repository
    shutil.copy(unformatted_file, repo_path)
    git_commit(unformatted_file.name, "initial test commit")

    # delete the file and commit the file
    os.remove(repo_path / "unformatted.py")
    git_commit(unformatted_file.name, "remove unformatted python file")

    # test that the file is no longer in repository
    # and that there are no errors thrown by pre-commit hook
    assert "unformatted.py" not in os.listdir(repo_path)


def test_non_python_file(repository):
    # add a non-python file and commit to repository
    shutil.copy(text_file, repo_path)
    git_commit(text_file.name, "initial test commit")

    # test that the file was unformatted
    # and that there were no errors thrown by pre-commit hook
    assert filecmp.cmp(text_file, repo_path / text_file.name) is True


def test_amend_commit(repository):
    """for reformatting pre-existing files"""
    formatted_file = test_files / "formatted2.py"
    # add file and commit to the repository
    shutil.copy(unformatted_file, repo_path)
    git_commit(unformatted_file.name, "initial test commit")

    # edit python file
    with open(repo_path / "unformatted.py", "a") as f:
        f.write("ugly_list_2 = ['hey' \n\n,\n'im a list', \n\t\t\n2]")

    # do an amend commit
    git_commit((repo_path / "unformatted.py").name, "add text and reformat", True)

    assert filecmp.cmp(repo_path / "unformatted.py", formatted_file) is True
