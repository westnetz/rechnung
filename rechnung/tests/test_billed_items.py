import pytest
import rechnung.cli as cli
import rechnung.settings as settings
import yaml

from click.testing import CliRunner
from shutil import copytree
from pathlib import Path


def test_billed_items(cli_billed_tests_data_path):
    """
    Tests if billing items works as expected.
    """
    cli1, path = cli_billed_tests_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["bill-items", "2019", "10"])
    expected_results = [
        "Billing items for month 10 in 2019.",
        "Ignoring 1001 with start 2030-06-01",
        "Billing items for 1000.",
        "Billing items for 1002.",
    ]
    print(result.output)
    for e_r in expected_results:
        assert e_r in result.output

    # Checking if it fails, if run again on the same year/month
    result = runner.invoke(cli1, ["bill-items", "2019", "10"])
    expected_results = [
        "Billing items for month 10 in 2019.",
        "Ignoring 1001 with start 2030-06-01",
        "Billing items for 1000.",
        "2019-10 already billed for 1000",
        "Billing items for 1002.",
        "2019-10 already billed for 1002",
    ]
    for e_r in expected_results:
        assert e_r in result.output

    result = runner.invoke(cli1, ["bill-items", "2019", "11"])
    result = runner.invoke(cli1, ["bill-items", "2019", "12"])
    billed_items_1000_path = path.joinpath(s.billed_items_dir, "1000.yaml")
    billed_items_1001_path = path.joinpath(s.billed_items_dir, "1001.yaml")
    billed_items_1002_path = path.joinpath(s.billed_items_dir, "1002.yaml")
    assert billed_items_1000_path.is_file()
    assert not billed_items_1001_path.is_file()
    assert billed_items_1002_path.is_file()
