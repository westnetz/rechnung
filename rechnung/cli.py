import click
import os
import sys

from .settings import get_settings_from_cwd, copy_assets, create_required_settings_file
from .invoice import create_invoices, render_invoices, send_invoices
from .contract import create_contracts, render_contracts, send_contract, get_contracts

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
@click.argument("year", type=int)
@click.argument("month", type=int)
def create(year, month):
    """
    Mass create invoices.
    """
    print("Creating invoices...")
    settings = get_settings_from_cwd(cwd)
    create_invoices(settings, year, month)


@cli1.command()
def print_contracts():
    """
    Print an overview of all contracs
    """
    for cid, contract in get_contracts(cwd).items():
        if not "slug" in contract:
            contract["slug"] = contract["email"]
        print("{cid}: {slug} {opening} {monthly}€".format(**contract))


@cli1.command()
def print_stats():
    """
    Print stats about the contracts
    """
    contracts = get_contracts(cwd).values()
    print(f"{len(contracts)} contracts in total")

    total_monthly = sum(map(lambda c: int(c["monthly"]), contracts))
    print(f"{total_monthly}€ per month")


@cli1.command()
def render():
    """
    Render all unrendered invoices.
    """
    print("Rendering invoices and contracts...")
    settings = get_settings_from_cwd(cwd)
    render_invoices(settings)
    render_contracts(settings)


@cli1.command()
@click.argument("year", type=int)
@click.argument("month", type=int)
def send(year, month):
    """
    Send invoices by email.
    """
    print(f"Sending invoices for {year}.{month:02}")
    settings = get_settings_from_cwd(cwd)
    send_invoices(settings, year, month)


@cli1.command()
@click.argument("cid", type=int)
def send_contract_mail(cid):
    """
    Send contract by email.
    """
    print(f"Sending contract {cid}")
    settings = get_settings_from_cwd(cwd)
    send_contract(settings, cid)


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    cli()
