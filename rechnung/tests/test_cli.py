import pytest
import rechnung.cli as cli
import rechnung.settings as settings
import yaml

from click.testing import CliRunner
from shutil import copytree
from pathlib import Path


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
    """
    Test the print-stats function.
    It checks if the amount of active contracts and the total income per month is calculated
    correctly.
    """
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["print-stats"])
    assert result.output == "2 active contracts of 3 in total\n108.66€ per month\n"


def test_print_contracts(cli_test_data_path):
    """
    Tests the print-contracts function.
    Tests is the names, total amounts are given correctly.
    """
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["print-contracts"])
    assert (
        result.output
        == """1000: Martha Muster 2019-06-01 60.21€
1001: Murks GmbH, Mike Murks 2030-06-01 13.37€
1002: Frank Nord 2019-06-01 48.45€
"""
    )


def test_invoice_create(cli_test_data_path):
    """
    Tests if the create-invoices function works properly.
    It checks for existence and absence of the expected files as well as the correct
    total_gross, total_net and total_vat amounts.
    """
    cli1, path = cli_test_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    runner.invoke(cli1, ["create-invoices", "2019", "10"])
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


def test_invoice_create_force(cli_test_data_path):
    """
    Tests if the --force-recreate function of the create-invoices command works as expected.
    I.e. invoices are not overwritten if the force option is not given.
    """
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(cli1, ["create-invoices", "2019", "10"])
    expected_results = [
        "Ignoring 1001 with start 2030-06-01",
        "Creating invoice yaml 1000.2019.10",
        "invoices/1000/1000.2019.10.yaml already exists.",
        "Creating invoice yaml 1002.2019.10",
        "invoices/1002/1002.2019.10.yaml already exists.",
    ]
    for expected_result in expected_results:
        assert expected_result in expected_results
    result = runner.invoke(cli1, ["create-invoices", "2019", "10", "--force-recreate"])
    assert "already exists" not in result.output


def test_invoice_create_cid_only(cli_test_data_path):
    cli1, path = cli_test_data_path
    runner = CliRunner()
    result = runner.invoke(
        cli1, ["create-invoices", "2019", "10", "--cid-only=1000", "--force-recreate"]
    )
    assert "1002" not in result.output
    assert "already exists" not in result.output


def test_invoice_render(cli_test_data_path):
    """
    Tests if the render-all function results in the correct invoices being created.
    As pdf testing is difficult it only checks for existence of the pdfs, assuming
    that the render process worked as expected.
    """
    cli1, path = cli_test_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    runner.invoke(cli1, ["render-all"])
    assert path.joinpath(s.invoices_dir, "1000", "1000.2019.10.pdf").is_file()
    assert not path.joinpath(s.invoices_dir, "1001", "1001.2019.10.pdf").is_file()
    assert path.joinpath(s.invoices_dir, "1002", "1002.2019.10.pdf").is_file()


def test_postbank_statement_import(cli_test_data_path):
    cli1, path = cli_test_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(
        cli1, ["import-bank-statement", str(path / "bank_statements" / "postbank.csv")]
    )
    print(result.output)
    print(result.exit_code)
    assert result.exit_code == 0
    assert result.output.startswith("Importing bank statement")
    payment_filename = result.output.split("\n")[1].split()[2]
    with open(payment_filename) as payment_file:
        payment_data = yaml.load(payment_file, Loader=yaml.FullLoader)
    with open(s.payments_dir / "postbank.yaml") as payment_master:
        master_data = yaml.load(payment_master, Loader=yaml.FullLoader)
    for i, j in zip(payment_data, master_data):
        assert i == j
