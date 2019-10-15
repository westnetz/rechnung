import pytest
import rechnung.cli as cli
import rechnung.settings as settings

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
        expected_elements.remove(element.name)
    assert not len(expected_elements)


def test_print_stats(cli_test_data_path):
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["print-stats"])
    assert "108.66" in result.output


#    assert False
