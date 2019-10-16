import click
import os
import arrow

from .settings import get_settings_from_cwd, copy_assets, create_required_settings_file
from .invoice import create_invoices, render_invoices, send_invoices
from .contract import render_contracts, send_contract, get_contracts

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
    print(f"Initializing in {cwd}...")

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
    settings = get_settings_from_cwd(cwd)
    for cid, data in get_contracts(settings).items():
        slug = data.get("email", "unknown")
        total_monthly = sum(
            map(lambda i: i.get("quantity", 1) * i["price"], data["items"])
        )
        print(f"{cid}: {slug} {data['start']} {total_monthly}€")


@cli1.command()
def print_stats():
    """
    Print stats about the contracts
    """
    settings = get_settings_from_cwd(cwd)
    contracts = get_contracts(settings).items()
    now = arrow.now()
    contracts_totals = list()
    for cid, data in contracts:
        # fetch dates, if no end date is set or know, it will be set to 1 year in the future
        start_date = arrow.get(data["start"])
        end_date = arrow.get(data.get("end", now + arrow.arrow.relativedelta(years=1)))
        if start_date > now or now > end_date:
            continue

        contracts_totals.append(
            sum(map(lambda i: i.get("quantity", i) * i["price"], data["items"]))
        )
    print(f"{len(contracts_totals)} active contracts of {len(contracts)} in total")
    print(f"{sum(contracts_totals):.2f}€ per month")


@cli1.command()
def render():
    """
    Render all unrendered invoices and contracs
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
