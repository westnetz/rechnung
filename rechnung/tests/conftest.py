import pytest
import rechnung.cli as cli
import rechnung.settings as settings
import yaml

from click.testing import CliRunner
from shutil import copytree
from pathlib import Path


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
    tmp_path = tmp_path_factory.getbasetemp() / "rechnung_initialized"
    tmp_path.mkdir()
    cli.cwd = tmp_path
    runner = CliRunner()
    runner.invoke(cli.cli1, ["init"])
    return tmp_path


@pytest.fixture(scope="session")
def cli_test_data_path(tmp_path_factory):
    """
    Returns a path where rechnung is initialized in order to verify correct creation
    of directories and files
    """
    tmp_path = tmp_path_factory.getbasetemp()
    cli_path = tmp_path / "rechnung_test_data"
    copytree(Path("rechnung/tests/fixtures"), cli_path)
    cli.cwd = cli_path
    return cli.cli1, cli_path


@pytest.fixture(scope="session")
def cli_billed_tests_data_path(tmp_path_factory):
    """
    Returns a path where rechnung is initialized in order to verify correct creation
    of the billed_items and invoice creation workflow
    """
    tmp_path = tmp_path_factory.getbasetemp()
    cli_path = tmp_path / "rechnung_billed_test_data"
    copytree(Path("rechnung/tests/fixtures"), cli_path)
    cli.cwd = cli_path
    return cli.cli1, cli_path
