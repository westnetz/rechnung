import click
import os
import sys

from .initialize import init_dir, check_dir
from .convert_customers import convert_customers
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
@click.option(
    "--without-samples",
    is_flag=True,
    help="Create working directory without sample customers",
    default=False
)
def init(without_samples):
    """
    Create the directory structure in the current directory.
    """
    print("Initializing...")

    try:
        init_dir(cwd, without_samples)
    except Exception:
        print("Failed. :/")
        sys.exit(1)

    print("Finished.")


@cli1.command()
def check():
    """
    Check the directory structure in the current working directory.
    """
    error = check_dir(cwd)
    sys.exit(error)


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
    print("Creating contracts...")
    create_contracts(cwd)

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


@cli1.command()
@click.argument(
    "cdir", type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True)
)
def import_customers(cdir):
    """
    Import customers and convert them to the new format.
    """
    print("Importing customers from {}".format(cdir))
    convert_customers(cwd, cdir)


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    cli()
