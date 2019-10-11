import click
import pytest
import rechnung.cli as cli
import rechnung.settings as settings

from click.testing import CliRunner
from pathlib import Path
from mock import patch
import os


@pytest.fixture
def cli_path(tmp_path):
    """
    Returnes the click.CommandGroup of cli.py holding all executeable commands,
    but with the module withe variable "cwd" overwritten to a temporary path. This is 
    required as the current working directory is determined by os.getcwd() on import
    olf rechnung.cli
    """
    cli.cwd = tmp_path
    return cli.cli1, tmp_path


@pytest.fixture(scope="session")
def initialized_path(tmp_path_factory):
    """
    Returns a path where rechnung is initialized in order to verify correct creation
    of directories and files
    """
    tmp_path = tmp_path_factory.getbasetemp().joinpath("rechnung_initialized").mkdir()
    cli.cwd = tmp_path
    runner = CliRunner()
    result = runner.invoke(cli.cli1, ["init"])
    return tmp_path


def test_init_exit_code(cli_path):
    """
    Tests if the initialization function returns the correct exit codes.
    """
    cli1, path = cli_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["init"])
    assert result.exit_code == 0
    # The second run should fail, as various files already exist:
    result = runner.invoke(cli1, ["init"])
    assert result.exit_code == 1


def test_init_files_directories(initialized_path):
    """
    Test if the initialization creates a settings file and all directories ot be created.
    """
    expected_elements = ["settings.yaml"]
    for setting_k, setting_v in settings.optional_settings.items():
        if setting_k.endswith("_dir"):
            expected_elements.append(setting_v)
    for element in initialized_path.iterdir():
        print(f"x: {element.name}")
        expected_elements.remove(element.name)
    assert not len(expected_elements)
