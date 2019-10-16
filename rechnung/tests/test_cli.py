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
    assert result.output == "2 active contracts of 3 in total\n108.66€ per month\n"


def test_print_contracts(cli_test_data_path):
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["print-contracts"])
    assert (
        result.output
        == "1000: Martha Muster 2019-06-01 60.21€\n1001: Murks GmbH, Mike Murks 2030-06-01 13.37€\n1002: Frank Nord 2019-06-01 48.45€\n"
    )

def test_invoice_create(cli_test_data_path):
    cli1, path = cli_test_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["create", "2019", "10"])
    invoice_1000_path = path.joinpath(s.invoices_dir, "1000", "1000.2019.10.yaml")
    invoice_1002_path = path.joinpath(s.invoices_dir, "1002", "1002.2019.10.yaml")
    assert invoice_1000_path.is_file()
    assert not path.joinpath(s.invoices_dir, "1001", "1001.2019.10.yaml").is_file()
    assert invoice_1002_path.is_file()

    with open(invoice_1000_path) as infile:
        invoice_data = yaml.safe_load(infile)
        assert invoice_data["total_net"] == 50.6
        assert invoice_data["total_vat"] == 9.61
        assert invoice_data["total_gross"] == 60.21
    with open(invoice_1002_path) as infile:
        invoice_data = yaml.safe_load(infile)
        assert invoice_data["total_net"] == 40.71
        assert invoice_data["total_vat"] == 7.74
        assert invoice_data["total_gross"] == 48.45

def test_invoice_render(cli_test_data_path):
    cli1, path = cli_test_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["render-all"])
    assert path.joinpath(s.invoices_dir, "1000", "1000.2019.10.pdf").is_file()
    assert not path.joinpath(s.invoices_dir, "1001", "1001.2019.10.pdf").is_file()
    assert path.joinpath(s.invoices_dir, "1002", "1002.2019.10.pdf").is_file()

