"""
This test collections test the billed items workflow.

These tests depend on each other. So please be careful, when changing
the contents of the test, as a change in one function might break 
another.

First we create billed invoices on a fresh working directory. 
This is expected to fail, as there are no billed items yet. After
that, we create billed items and check for their correctness. Then
we create a single billed invoice, to check the single cid (cid-only) 
option. We finish, by creating billed invoices for the remaining cids
without that option. By that we cover most of the use cases, and possible
sources of errors that are known to us at the moment.
"""

import pytest
import rechnung.cli as cli
import rechnung.settings as settings
import yaml

from click.testing import CliRunner
from shutil import copytree
from pathlib import Path


def test_billed_invoice_without_billed_items(cli_billed_tests_data_path):
    """
    Tests if create-billed-invoice does not create any invoice,
    if there are no billed items present.
    """
    cli1, path = cli_billed_tests_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["create-billed-invoices", "2019.Q4"])
    expected_results = [
        "Creating billed invoice yaml 1000.2019.Q4",
        "No unbilled items found for 1000",
        "Creating billed invoice yaml 1001.2019.Q4",
        "No unbilled items found for 1001",
        "Creating billed invoice yaml 1002.2019.Q4",
        "No unbilled items found for 1002",
    ]
    for e_r in expected_results:
        assert e_r in result.output
    
    billed_items_1000_path = path.joinpath(s.billed_items_dir, "1000.yaml")
    billed_items_1001_path = path.joinpath(s.billed_items_dir, "1001.yaml")
    billed_items_1002_path = path.joinpath(s.billed_items_dir, "1002.yaml")
    assert not billed_items_1000_path.is_file()
    assert not billed_items_1001_path.is_file()
    assert not billed_items_1002_path.is_file()


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

    with open(billed_items_1000_path) as infile:
        billed_items_1000 = yaml.safe_load(infile)
    with open(Path("rechnung/tests/golden_masters/billed_items_1000.yaml")) as infile:
        billed_items_1000_golden_master = yaml.safe_load(infile)
    assert billed_items_1000 == billed_items_1000_golden_master
    with open(billed_items_1002_path) as infile:
        billed_items_1002 = yaml.safe_load(infile)
    with open(Path("rechnung/tests/golden_masters/billed_items_1002.yaml")) as infile:
        billed_items_1002_golden_master = yaml.safe_load(infile)
    assert billed_items_1002 == billed_items_1002_golden_master


def test_create_single_billed_invoice(cli_billed_tests_data_path):
    """
    Test the cid_only feature of the create-billed-invoices command.
    """
    cli1, path = cli_billed_tests_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["create-billed-invoices", "2019.Q4", "-c", "1000"])
    expected_results = [
        "Creating billed invoice yaml 1000.2019.Q4"
    ]
    unexpected_results = [
        "Creating billed invoice yaml 1001.2019.Q4"
        "Creating billed invoice yaml 1002.2019.Q4"
    ]
    
    # Check for correct output of the command
    for e_r in expected_results:
        assert e_r in result.output
    for u_r in unexpected_results:
        assert u_r not in result.output
   
    # Check if only the expected files exist
    invoice_1000_path = path.joinpath(s.invoices_dir, "1000", "1000.2019.Q4.yaml")
    invoice_1001_path = path.joinpath(s.invoices_dir, "1001", "1001.2019.Q4.yaml")
    invoice_1002_path = path.joinpath(s.invoices_dir, "1002", "1002.2019.Q4.yaml")
    assert invoice_1000_path.is_file()
    assert not invoice_1001_path.is_file()
    assert not invoice_1002_path.is_file()

    # Check the contents of the only invoice created
    with open(invoice_1000_path) as infile:
        invoice = yaml.safe_load(infile)
        assert len(invoice['items']) == 6
        assert invoice['total_gross'] == 180.63
        assert invoice['total_net'] == 151.79
        assert invoice['total_vat'] == 28.84

    # Check if invoice id correctly entered into billed_items
    billed_items_1000_path = path.joinpath(s.billed_items_dir, "1000.yaml")
    with open(billed_items_1000_path) as infile:
        billed_items_1000 = yaml.safe_load(infile)
        for billed_item in billed_items_1000:
            assert billed_item['invoice'] == '1000.2019.Q4'


def test_create_billed_invoices(cli_billed_tests_data_path):
    """
    Test the cid_only feature of the create-billed-invoices command.
    """
    cli1, path = cli_billed_tests_data_path
    s = settings.get_settings_from_cwd(path)
    runner = CliRunner()
    result = runner.invoke(cli1, ["create-billed-invoices", "2019.Q4"])
    expected_results = [
        "No unbilled items found for 1000",
        "No unbilled items found for 1001"
    ]
    unexpected_results = [
        "No unbilled items found for 1002"
    ]
    
    # Check for correct output of the command
    for e_r in expected_results:
        assert e_r in result.output
    for u_r in unexpected_results:
        assert u_r not in result.output
   
    # Check if only the expected files exist
    invoice_1000_path = path.joinpath(s.invoices_dir, "1000", "1000.2019.Q4.yaml")
    invoice_1001_path = path.joinpath(s.invoices_dir, "1001", "1001.2019.Q4.yaml")
    invoice_1002_path = path.joinpath(s.invoices_dir, "1002", "1002.2019.Q4.yaml")
    assert invoice_1000_path.is_file()
    assert not invoice_1001_path.is_file()
    assert invoice_1002_path.is_file()

    # Check the contents of the only invoice created
    with open(invoice_1002_path) as infile:
        invoice = yaml.safe_load(infile)
        assert len(invoice['items']) == 6
        assert invoice['total_gross'] == 145.35
        assert invoice['total_net'] == 122.14
        assert invoice['total_vat'] == 23.21

    # Check if invoice id correctly entered into billed_items
    billed_items_1002_path = path.joinpath(s.billed_items_dir, "1002.yaml")
    with open(billed_items_1002_path) as infile:
        billed_items_1002 = yaml.safe_load(infile)
        for billed_item in billed_items_1002:
            assert billed_item['invoice'] == '1002.2019.Q4'
