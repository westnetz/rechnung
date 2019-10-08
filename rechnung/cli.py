import click
import os
import sys

from .settings import get_settings_from_cwd, copy_assets, create_required_settings_file
from .invoice import create_invoices, render_invoices, send_invoices
from .contract import create_contracts, render_contracts, send_contract

cwd = os.getcwd()


@click.group()
def cli1():
    """
    rechnung command line interface.
    """
    pass


@cli1.command()
def init():
    """
    Create the directory structure in the current directory.
    """
    print("Initializing...")

    create_required_settings_file(cwd)
    settings = get_settings_from_cwd(cwd, create_non_existing_dirs=True)
    copy_assets(settings.assets_dir)

    print("Finished.")


@cli1.command()
@click.argument("start_date")
@click.argument("end_date")
@click.argument("n_months", type=int)
@click.argument("year")
@click.argument("suffix")
def create(start_date, end_date, n_months, year, suffix):
    """
    Mass create invoices.
    """
    print("Creating invoices...")
    create_invoices(cwd, start_date, end_date, n_months, year, suffix)


@cli1.command()
def contracts():
    """
    Mass create contracts.
    """
    print("Not yet implemented")


@cli1.command()
def render():
    """
    Render all unrendered invoices.
    """
    print("Rendering invoices and contracts...")
    render_invoices(cwd)
    render_contracts(cwd)


@cli1.command()
@click.argument("year_suffix")
def send(year_suffix):
    """
    Send invoices by email.
    """
    print("Sending invoices *.{}".format(year_suffix))
    send_invoices(cwd, year_suffix)


@cli1.command()
@click.argument("cid")
def send_contract_mail(cid):
    """
    Send contract by email.
    """
    print("Sending contract for customer {}".format(cid))
    send_contract(cwd, cid)


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    cli()
