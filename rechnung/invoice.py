import datetime
import locale
import os
import os.path
import yaml

from .config import get_config
from .settings import ASSETS_DIR
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
    send_email,
)


def fill_invoice_positions(positions, n_months, config):
    invoice_total_netto = float()
    invoice_total_ust = float()
    invoice_total_brutto = float()

    invoice_positions = []

    for n_e, position in enumerate(positions):
        final_quantity = n_months * position["quantity"]
        subtotal = round(final_quantity * position["price"], 2)

        invoice_positions.append(
            {
                "position": n_e + 1,
                "description": position["description"],
                "price": position["price"],
                "quantity": final_quantity,
                "subtotal": subtotal,
            }
        )

        invoice_total_netto += subtotal

    invoice_total_brutto = round(invoice_total_netto * (1.0 + config.vat / 100.0), 2)
    invoice_total_ust = round(invoice_total_brutto - invoice_total_netto, 2)

    return (
        invoice_positions,
        invoice_total_netto,
        invoice_total_ust,
        invoice_total_brutto,
    )


def generate_invoice(
    customer, positions, start_date, end_date, n_months, year, suffix, config
):

    invoice_positions, netto, ust, brutto = fill_invoice_positions(
        positions, n_months, config
    )

    invoice_data = {}
    invoice_data["address"] = customer["address"]
    invoice_data["cid"] = customer["cid"]
    invoice_data["date"] = datetime.datetime.now().strftime("%d. %B %Y")
    invoice_data["id"] = "{}.{}.{}".format(customer["cid"], year, suffix)
    invoice_data["period"] = "{} - {}".format(start_date, end_date)
    invoice_data["total_brutto"] = brutto
    invoice_data["total_netto"] = netto
    invoice_data["total_ust"] = ust
    invoice_data["vat"] = config.vat

    if "email" not in customer.keys():
        invoice_data["email"] = None
    else:
        invoice_data["email"] = customer["email"]

    return (invoice_data, invoice_positions)


def iterate_invoices(invoices_dir):
    """
    Generator which iterates over all customer directories and
    included invoice yamls, yields customer_invoice_dir and filename.
    """
    for d in os.listdir(invoices_dir):
        customer_invoice_dir = os.path.join(invoices_dir, d)
        if os.path.isdir(customer_invoice_dir):
            for filename in os.listdir(customer_invoice_dir):

                if not filename.endswith(".yaml"):
                    continue

                yield customer_invoice_dir, filename


def render_pdf_invoices(directory, template, config):

    logo_path = os.path.join(directory, ASSETS_DIR, "logo.svg")

    for customer_invoice_dir, filename in iterate_invoices(config.invoices_dir):
        if not os.path.isfile(
            "{}.pdf".format(os.path.join(customer_invoice_dir, filename[:-5]))
        ):
            with open(os.path.join(customer_invoice_dir, filename)) as yaml_file:
                invoice_data, invoice_positions = yaml.load(
                    yaml_file.read(), Loader=yaml.FullLoader
                )
            invoice_data["logo_path"] = logo_path
            invoice_data["company"] = config.company

            print("Rendering invoice pdf for {}".format(invoice_data["id"]))

            # Format data for printing
            for element in ["total_netto", "total_brutto", "total_ust"]:
                invoice_data[element] = locale.format_string(
                    "%.2f", invoice_data[element]
                )
            for position in invoice_positions:
                for key in ["price", "subtotal"]:
                    position[key] = locale.format_string("%.2f", position[key])

            invoice_html = template.render(
                positions=invoice_positions, invoice=invoice_data
            )

            invoice_pdf_filename = os.path.join(
                customer_invoice_dir, "{}.pdf".format(invoice_data["id"])
            )
            generate_pdf(
                invoice_html, config.invoice_css_filename, invoice_pdf_filename
            )


def save_invoice_yaml(invoices_dir, invoice_data, invoice_positions):
    invoice_customer_dir = os.path.join(invoices_dir, invoice_data["cid"])
    if not os.path.isdir(invoice_customer_dir):
        os.mkdir(invoice_customer_dir)

    outfilename = os.path.join(
        invoice_customer_dir, "{}.yaml".format(invoice_data["id"])
    )
    try:
        with open(outfilename, "x") as outfile:
            outfile.write(
                yaml.dump([invoice_data, invoice_positions], default_flow_style=False)
            )
    except FileExistsError:
        print("Invoice {} already exists.".format(outfilename))


def create_yaml_invoices(
    invoices_dir,
    customers,
    positions,
    start_date,
    end_date,
    n_months,
    year,
    suffix,
    config,
):

    for cid in customers.keys():
        print("Creating invoice yaml for {}".format(cid))
        invoice_data, invoice_positions = generate_invoice(
            customers[cid],
            positions[cid],
            start_date,
            end_date,
            n_months,
            year,
            suffix,
            config,
        )
        save_invoice_yaml(invoices_dir, invoice_data, invoice_positions)


def get_customers(customers_dir):
    customers = {}
    for filename in os.listdir(customers_dir):

        if not filename.endswith(".yaml"):
            continue

        origin_file = os.path.join(customers_dir, filename)
        with open(origin_file, "r") as infile:
            customer = yaml.load(infile, Loader=yaml.FullLoader)

        customers[customer["cid"]] = customer
    return customers


def get_positions(positions_dir):
    positions = {}
    for filename in os.listdir(positions_dir):

        if not filename.endswith(".yaml"):
            continue

        origin_file = os.path.join(positions_dir, filename)
        cid = filename.split(".")[0]
        with open(origin_file, "r") as infile:
            position = yaml.load(infile, Loader=yaml.FullLoader)
        positions[cid] = position
    return positions


def send_invoice_mails(config, mail_template, year_suffix):

    for d in os.listdir(config.invoices_dir):
        customer_invoice_dir = os.path.join(config.invoices_dir, d)
        if os.path.isdir(customer_invoice_dir):
            for filename in os.listdir(customer_invoice_dir):

                if not filename.endswith(".yaml"):
                    continue

                file_suffix = ".".join(filename.split(".")[-3:-1])

                if file_suffix != year_suffix:
                    continue

                with open(os.path.join(customer_invoice_dir, filename)) as yaml_file:
                    invoice_data, invoice_positions = yaml.load(
                        yaml_file, Loader=yaml.FullLoader
                    )

                if invoice_data["email"] is None:
                    continue

                invoice_pdf_path = os.path.join(
                    customer_invoice_dir, "{}.pdf".format(filename[:-5])
                )
                invoice_pdf_filename = "Westnetz_Rechnung_{}.pdf".format(filename[:-5])
                invoice_mail_text = mail_template.render(invoice=invoice_data)
                invoice_pdf = get_pdf(invoice_pdf_path)

                invoice_receiver = invoice_data["email"]

                invoice_email = generate_email_with_pdf_attachment(
                    invoice_receiver,
                    config.sender,
                    config.invoice_mail_subject,
                    invoice_mail_text,
                    invoice_pdf,
                    invoice_pdf_filename,
                )

                print("Sending invoice {}".format(invoice_data["id"]))

                send_email(
                    invoice_email,
                    config.server,
                    config.username,
                    config.password,
                    config.insecure,
                )


def create_invoices(directory, start_date, end_date, n_months, year, suffix):
    config = get_config(directory)
    customers = get_customers(config.customers_dir)
    positions = get_positions(config.positions_dir)
    create_yaml_invoices(
        config.invoices_dir,
        customers,
        positions,
        start_date,
        end_date,
        n_months,
        year,
        suffix,
        config,
    )


def render_invoices(directory):
    config = get_config(directory)
    template = get_template(config.invoice_template_filename)
    render_pdf_invoices(directory, template, config)


def send_invoices(directory, year_suffix):
    config = get_config(directory)
    mail_template = get_template(config.invoice_mail_template_filename)
    send_invoice_mails(config, mail_template, year_suffix)
