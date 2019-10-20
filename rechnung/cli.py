import arrow
import click
import os
import rechnung.invoice as invoice
import rechnung.contract as contract
import rechnung.payment as payment

from .settings import get_settings_from_cwd, copy_assets, create_required_settings_file
from .transactions import read_csv_files

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
@click.option("-c", "--cid-only")
@click.option("-f", "--force-recreate", "force", is_flag=True)
def create_invoices(year, month, cid_only=None, force=False):
    """
    Mass create invoices.
    """
    print("Creating invoices...")
    settings = get_settings_from_cwd(cwd)
    invoice.create_invoices(settings, year, month, cid_only, force)


@cli1.command()
def print_contracts():
    """
    Print an overview of all contracs
    """
    settings = get_settings_from_cwd(cwd)
    for cid, data in contract.get_contracts(settings).items():
        company_name = data.get("company", "")
        name = data.get("name", "unknown")
        if company_name:
            company_name += f", {name}"
        else:
            company_name = name
        total_monthly = sum(
            map(lambda i: i.get("quantity", 1) * i["price"], data["items"])
        )
        print(f"{cid}: {company_name} {data['start']} {total_monthly}€")


@cli1.command()
@click.argument("year", type=int)
@click.argument("month", type=int)
def print_csv(year, month):
    """
    Parse CSV files for a specific year/month combo
    """
    settings = get_settings_from_cwd(cwd)
    print(f"Parsing CSV files for {year}{month}")
    for transaction in read_csv_files(settings, year, month):
        print("{date}: {type[0]} {amount:>6}€ {sender}".format(**transaction))


@cli1.command()
def print_stats():
    """
    Print stats about the contracts
    """
    settings = get_settings_from_cwd(cwd)
    contracts = contract.get_contracts(settings).items()
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
def render_all():
    """
    Render all unrendered invoices and contracs
    """
    print("Rendering invoices and contracts...")
    settings = get_settings_from_cwd(cwd)
    invoice.render_invoices(settings)
    contract.render_contracts(settings)


@cli1.command()
@click.argument("year", type=int)
@click.argument("month", type=int)
@click.option("-c", "--cid_only")
@click.option("-f", "--force-resend", "force", is_flag=True)
def send_invoices(year, month, cid_only=None, force=False):
    """
    Send invoices by email.
    """
    print(f"Sending invoices for {year}.{month:02}")
    settings = get_settings_from_cwd(cwd)
    invoice.send_invoices(settings, year, month, cid_only, force)


@cli1.command()
@click.argument("cid", type=int)
def send_contract(cid):
    """
    Send contract by email.
    """
    print(f"Sending contract {cid}")
    settings = get_settings_from_cwd(cwd)
    contract.send_contract(settings, cid)


@cli1.command()
@click.argument("bank_statement_file", type=click.Path(exists=True))
def import_bank_statement(bank_statement_file):
    """
    Import a bank statement to be annotated with cids
    and used in reports.
    """
    print(f"Importing bank statement {bank_statement_file}...")
    settings = get_settings_from_cwd(cwd)
    outfilename = payment.import_bank_statement_from_file(bank_statement_file, settings)
    print(f"Saved as {outfilename}")


@cli1.command()
@click.argument("cid")
def report(cid):
    """
    Create a report for a customer.
    """
    print(f"Reporting customer {cid}...")
    settings = get_settings_from_cwd(cwd)
    payment.report_customer(cid, settings)


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    cli()
