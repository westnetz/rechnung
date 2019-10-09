import datetime
import locale
import os
import os.path
from pathlib import Path
import yaml

from .settings import get_settings_from_cwd
from .contract import get_contracts
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
    send_email,
)


def fill_invoice_items(settings, items):
    invoice_total_net = float()
    invoice_total_vat = float()
    invoice_total_gross = float()

    invoice_items = []

    for n_e, item in enumerate(items):
        final_quantity = item.get("quantity", 1)
        subtotal = round(final_quantity * item["price"], 2)

        invoice_items.append(
            {
                "item": n_e + 1,
                "description": item["description"],
                "price": item["price"],
                "quantity": final_quantity,
                "subtotal": subtotal,
            }
        )

        invoice_total_gross += subtotal

    invoice_total_net = round(invoice_total_gross / (1.0 + settings.vat / 100.0), 2)
    invoice_total_vat = round(invoice_total_gross - invoice_total_net, 2)

    return (invoice_items, invoice_total_net, invoice_total_vat, invoice_total_gross)


def generate_invoice(settings, contract, year, month):
    invoice_items, net, vat, gross = fill_invoice_items(settings, contract["items"])

    invoice_data = {}
    invoice_data["address"] = contract.get("address", ["", "", ""])
    invoice_data["cid"] = contract["cid"]
    invoice_data["date"] = datetime.datetime.now().strftime(
        settings.delivery_date_format
    )
    invoice_data["id"] = f"{contract['cid']}.{year}.{mont:02}"
    invoice_data["period"] = "{}-{}".format(year, month)
    invoice_data["total_gross"] = gross
    invoice_data["total_net"] = net
    invoice_data["total_vat"] = vat
    invoice_data["vat"] = settings.vat
    invoice_data["email"] = contract["email"]
    invoice_data["items"] = invoice_items
    return invoice_data


def iterate_invoices(invoices_dir):
    """
    Generator which iterates over all contract directories and
    included invoice yamls, yields contract_invoice_dir and filename.
    """
    for d in os.listdir(invoices_dir):
        contract_invoice_dir = os.path.join(invoices_dir, d)
        if os.path.isdir(contract_invoice_dir):
            for filename in os.listdir(contract_invoice_dir):

                if not filename.endswith(".yaml"):
                    continue

                yield contract_invoice_dir, filename


def render_invoices(settings):
    template = get_template(settings.invoice_template_file)
    logo_path = Path(settings.assets_dir / "logo.svg")

    for contract_invoice_dir, filename in iterate_invoices(settings.invoices_dir):
        if not os.path.isfile(
            "{}.pdf".format(os.path.join(contract_invoice_dir, filename[:-5]))
        ):
            with open(os.path.join(contract_invoice_dir, filename)) as yaml_file:
                invoice_data = yaml.safe_load(yaml_file.read())
            invoice_data["logo_path"] = logo_path
            invoice_data["company"] = settings.company

            print("Rendering invoice pdf for {}".format(invoice_data["id"]))

            # Format data for printing
            for element in ["total_net", "total_gross", "total_vat"]:
                invoice_data[element] = locale.format_string(
                    "%.2f", invoice_data[element]
                )
            for item in invoice_data["items"]:
                for key in ["price", "subtotal"]:
                    item[key] = locale.format_string("%.2f", item[key])

            invoice_html = template.render(invoice=invoice_data)

            invoice_pdf_filename = os.path.join(
                contract_invoice_dir, "{}.pdf".format(invoice_data["id"])
            )
            generate_pdf(
                invoice_html, settings.invoice_css_asset_file, invoice_pdf_filename
            )


def save_invoice_yaml(settings, invoice_data):
    invoice_contract_dir = Path(settings.invoices_dir / invoice_data["cid"])

    if not os.path.isdir(invoice_contract_dir):
        os.mkdir(invoice_contract_dir)

    outfilename = invoice_contract_dir / f"{invoice_data['id']}.yaml"
    try:
        with open(outfilename, "x") as outfile:
            outfile.write(yaml.dump(invoice_data, default_flow_style=False))
    except FileExistsError:
        print("Invoice {} already exists.".format(outfilename))


def create_invoices(settings, year, month):
    contracts = get_contracts(settings)
    create_yaml_invoices(settings, contracts, year, month)


def create_yaml_invoices(settings, contracts, year, month):
    for cid, contract in contracts.items():
        print("Creating invoice yaml for {}".format(cid))
        invoice_data = generate_invoice(settings, contract, year, month)
        save_invoice_yaml(settings, invoice_data)


def send_invoices(settings, year, month):
    mail_template = get_template(settings.invoice_mail_template_file)

    for d in os.listdir(settings.invoices_dir):
        customer_invoice_dir = os.path.join(settings.invoices_dir, d)
        if os.path.isdir(customer_invoice_dir):
            for filename in os.listdir(customer_invoice_dir):
                if not filename.endswith(".yaml"):
                    continue

                file_suffix = ".".join(filename.split(".")[-3:-1])

                if file_suffix != f"{year}.{month:02}":
                    continue

                with open(os.path.join(customer_invoice_dir, filename)) as yaml_file:
                    invoice_data = yaml.safe_load(yaml_file)

                invoice_pdf_path = os.path.join(
                    customer_invoice_dir, f"{filename[:-5]}.pdf"
                )
                invoice_pdf_filename = f"{settings.company} {filename[:-5]}.pdf"
                invoice_mail_text = mail_template.render(invoice=invoice_data)
                invoice_pdf = get_pdf(invoice_pdf_path)

                invoice_receiver = invoice_data["email"]

                invoice_email = generate_email_with_pdf_attachment(
                    invoice_receiver,
                    settings.sender,
                    settings.invoice_mail_subject,
                    invoice_mail_text,
                    invoice_pdf,
                    invoice_pdf_filename,
                )

                print(f"Sending invoice {invoice_data['id']}")

                print(invoice_email)

                send_email(
                    invoice_email,
                    settings.server,
                    settings.username,
                    settings.password,
                    settings.insecure,
                )
