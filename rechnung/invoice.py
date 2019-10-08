import datetime
import locale
import os
import os.path
import yaml

from .settings import get_settings_from_cwd
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
    send_email,
)


def fill_invoice_positions(positions, n_months, settings):
    invoice_total_net = float()
    invoice_total_vat = float()
    invoice_total_gross = float()

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

        invoice_total_gross += subtotal

    invoice_total_net = round(invoice_total_gross / (1.0 + settings.vat / 100.0), 2)
    invoice_total_vat = round(invoice_total_gross - invoice_total_net, 2)

    return (
        invoice_positions,
        invoice_total_net,
        invoice_total_vat,
        invoice_total_gross,
    )


def generate_invoice(
    customer, positions, start_date, end_date, n_months, year, suffix, settings
):

    invoice_positions, net, vat, gross = fill_invoice_positions(
        positions, n_months, settings
    )

    invoice_data = {}
    invoice_data["address"] = customer["address"]
    invoice_data["cid"] = customer["cid"]
    invoice_data["date"] = datetime.datetime.now().strftime("%d. %B %Y")
    invoice_data["id"] = "{}.{}.{}".format(customer["cid"], year, suffix)
    invoice_data["period"] = "{} - {}".format(start_date, end_date)
    invoice_data["total_gross"] = gross
    invoice_data["total_net"] = net
    invoice_data["total_vat"] = vat
    invoice_data["vat"] = settings.vat

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


def render_pdf_invoices(directory, template, settings):

    logo_path = os.path.join(settings.assets_dir, "logo.svg")

    for customer_invoice_dir, filename in iterate_invoices(settings.invoices_dir):
        if not os.path.isfile(
            "{}.pdf".format(os.path.join(customer_invoice_dir, filename[:-5]))
        ):
            with open(os.path.join(customer_invoice_dir, filename)) as yaml_file:
                invoice_data, invoice_positions = yaml.load(
                    yaml_file.read(), Loader=yaml.FullLoader
                )
            invoice_data["logo_path"] = logo_path
            invoice_data["company"] = settings.company

            print("Rendering invoice pdf for {}".format(invoice_data["id"]))

            # Format data for printing
            for element in ["total_net", "total_gross", "total_vat"]:
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
                invoice_html, settings.invoice_css_asset_file, invoice_pdf_filename
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
    settings,
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
            settings,
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


def send_invoice_mails(settings, mail_template, year_suffix):

    for d in os.listdir(settings.invoices_dir):
        customer_invoice_dir = os.path.join(settings.invoices_dir, d)
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
                    settings.sender,
                    settings.invoice_mail_subject,
                    invoice_mail_text,
                    invoice_pdf,
                    invoice_pdf_filename,
                )

                print("Sending invoice {}".format(invoice_data["id"]))

                send_email(
                    invoice_email,
                    settings.server,
                    settings.username,
                    settings.password,
                    settings.insecure,
                )


def create_invoices(directory, start_date, end_date, n_months, year, suffix):
    settings = get_settings_from_cwd(directory)
    customers = get_customers(settings.customers_dir)
    positions = get_positions(settings.positions_dir)
    create_yaml_invoices(
        settings.invoices_dir,
        customers,
        positions,
        start_date,
        end_date,
        n_months,
        year,
        suffix,
        settings,
    )


def render_invoices(directory):
    settings = get_settings_from_cwd(directory)
    template = get_template(settings.invoice_template_file)
    render_pdf_invoices(directory, template, settings)


def send_invoices(directory, year_suffix):
    settings = get_settings_from_cwd(directory)
    mail_template = get_template(settings.invoice_mail_template_file)
    send_invoice_mails(settings, mail_template, year_suffix)
