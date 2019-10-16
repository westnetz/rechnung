import click
import os

from .settings import get_settings_from_cwd, copy_assets, create_required_settings_file
import rechnung.invoice as invoice
import rechnung.contract as contract

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
@click.option("-c", "--cid-only")
@click.option("-f", "--force-recreate", "force", is_flag=True)
def create_invoices(year: int, month: int, cid_only: int = None, force: bool = False):
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
        slug = data.get("slug", "unknown")
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
    contracts = contract.get_contracts(settings).values()
    print(f"{len(contracts)} contracts in total")

    total_monthly = sum(
        map(
            lambda x: x[0].get("quantity", 1) * x[0]["price"],
            list(map(lambda i: i["items"], contracts)),
        )
    )
    print(f"{total_monthly:.2f}€ per month")


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
def send_invoices(year: int, month: int, cid_only: int = None, force: bool = False):
    """
    Send invoices by email.
    """
    print(f"Sending invoices for {year}.{month:02}")
    settings = get_settings_from_cwd(cwd)
    invoice.send_invoices(settings, year, month, cid_only, force)


@cli1.command()
@click.option("-c", "--cid")
@click.option("-s", "--slug")
def send_contract(cid: int = None, slug: str = None):
    """
    Send contract by email based on cid or slug

    Args:
        cid (int): contract ID to send to
        slug (str): contract slug to send to
    """
    settings = get_settings_from_cwd(cwd)
    cid, c = contract.get_contracts(settings, cid_only=cid, slug=slug).popitem()
    if c:
        print(f"Sending contract {c['slug']} - {cid}")
        contract.send_contract(settings, cid)
    else:
        print("Contract not found")


cli = click.CommandCollection(sources=[cli1])

if __name__ == "__main__":
    cli()
