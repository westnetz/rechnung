import arrow
import datetime
import locale
import yaml

from .contract import get_contracts
from .helpers import generate_pdf, get_template, generate_email, send_email


def fill_invoice_items(settings, items):
    """
    Calculates the items which will appear on the invoice, as well as the total_gross,
    total_net and total_vat value.
    """
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
    """
    Creates an invoice, i.e. calls the fill_invoice_items function, to get
    all the numbers right, as well as filling all the remaining required meta
    information about the customer.

    It returns the invoice dict.
    """
    invoice_items, net, vat, gross = fill_invoice_items(settings, contract["items"])

    invoice_data = {}
    invoice_data["address"] = contract.get("address", ["", "", ""])
    invoice_data["cid"] = contract["cid"]
    invoice_data["date"] = datetime.datetime.now().strftime(
        settings.delivery_date_format
    )
    invoice_data["email"] = contract["email"]
    invoice_data["id"] = f"{contract['cid']}.{year}.{month:02}"
    invoice_data["items"] = invoice_items
    invoice_data["period"] = f"{year}.{month}"
    invoice_data["total_gross"] = gross
    invoice_data["total_net"] = net
    invoice_data["total_vat"] = vat
    invoice_data["vat"] = settings.vat
    return invoice_data


def iterate_invoices(settings):
    """
    Generator which iterates over all contract directories and
    included invoice yamls, yields contract_invoice_dir and filename.
    """
    for d in settings.invoices_dir.iterdir():
        contract_invoice_dir = settings.invoices_dir / d
        if contract_invoice_dir.is_dir():
            for filename in contract_invoice_dir.glob("*.yaml"):
                yield contract_invoice_dir, filename


def render_invoices(settings):
    """
    Renders all invoices and saves pdfs to settings.invoices_dir.
    """
    template = get_template(settings.invoice_template_file)

    for contract_invoice_dir, filename in iterate_invoices(settings):
        invoice_pdf_filename = filename.with_suffix(".pdf")
        if not invoice_pdf_filename.is_file():
            with open(filename) as yaml_file:
                invoice_data = yaml.safe_load(yaml_file.read())
            invoice_data.update(settings._asdict())

            print(f"Rendering invoice pdf for {invoice_data['id']}")

            # Format data for printing
            for element in ["total_net", "total_gross", "total_vat"]:
                invoice_data[element] = locale.format_string(
                    "%.2f", invoice_data[element]
                )
            for item in invoice_data["items"]:
                for key in ["price", "subtotal"]:
                    item[key] = locale.format_string("%.2f", item[key])

            invoice_html = template.render(**invoice_data)

            generate_pdf(
                invoice_html, settings.invoice_css_asset_file, invoice_pdf_filename
            )
        else:
            print(f"Invoice {invoice_pdf_filename} already exists")


def save_invoice_yaml(settings, invoice_data, force=False):
    """
    Saves the invoice_data to a yaml file in settings.invoices_dir.
    """
    invoice_contract_dir = settings.invoices_dir / invoice_data["cid"]

    if not invoice_contract_dir.is_dir():
        invoice_contract_dir.mkdir()

    invoice_path = invoice_contract_dir / f"{invoice_data['id']}.yaml"
    if not invoice_path.is_file() or force:
        with open(invoice_path, "w") as invoice_fp:
            invoice_fp.write(yaml.dump(invoice_data, default_flow_style=False))
    else:
        print(f"Invoice {invoice_path} already exists.")


def create_invoices(settings, year, month, cid_only=None, force=False):
    """
    Bulk creates invoice yaml files for a specific month-year-combination.
    """
    if force:
        print("Force create enabled")

    if cid_only:
        print(f"Only creating to {cid_only}")

    contracts = get_contracts(settings, year, month, cid_only)
    for cid, contract in contracts.items():
        print(f"Creating invoice yaml {cid}.{year}.{month}")
        invoice_data = generate_invoice(settings, contract, year, month)
        save_invoice_yaml(settings, invoice_data, force)


def save_invoice_yaml(settings, invoice_data, force=False):
    """
    Saves the invoice_data to a yaml file in settings.invoices_dir.
    """
    invoice_contract_dir = settings.invoices_dir / invoice_data["cid"]

    if not invoice_contract_dir.is_dir():
        invoice_contract_dir.mkdir()

    invoice_path = invoice_contract_dir / f"{invoice_data['id']}.yaml"
    if not invoice_path.is_file() or force:
        with open(invoice_path, "w") as invoice_fp:
            invoice_fp.write(yaml.dump(invoice_data, default_flow_style=False))
    else:
        print(f"Invoice {invoice_path} already exists.")


class NoUnbilledItemsFound(Exception):
    pass


def get_period_from_item_keys(item_keys):
    item_dates = [arrow.get(key) for key in item_keys]
    start = sorted(map(lambda x: x.floor("month"), item_dates))[0]
    end = sorted(map(lambda x: x.ceil("month"), item_dates))[-1]
    return (start, end)


def generate_billed_invoice(settings, contract, suffix):
    """
    Creates an invoice from the already billed items, i.e. collects all unbilled items
    adds it to the invoice, and enters the invoice number into the billed items.

    It returns the invoice dict.
    """
    billed_items = get_billed_items(settings, contract["cid"])
    invoice_date = arrow.now().format("D.M.YYYY", locale=settings.arrow_locale)
    invoice_id = f"{contract['cid']}.{suffix}"

    net = float()
    vat = float()
    gross = float()

    invoice_items = []
    item_keys = []
    for billed_item in billed_items:
        if not billed_item["invoice"]:
            invoice_items.append(
                {
                    "item": len(invoice_items) + 1,
                    "description": billed_item["description"],
                    "price": billed_item["price"],
                    "quantity": billed_item["quantity"],
                    "subtotal": billed_item["subtotal"],
                }
            )
        item_keys.append(billed_item["key"])
        billed_item["invoice"] = invoice_id
        gross += billed_item["subtotal"]

    net = round(gross / (1.0 + settings.vat / 100.0), 2)
    vat = round(gross - net, 2)

    # If there are no unbilled items, an exception is raised, to be cought
    # in the caller function
    if not len(invoice_items):
        raise NoUnbilledItemsFound

    invoice_period = get_period_from_item_keys(item_keys)
    invoice_period_string = "{} - {}".format(
        invoice_period[0].format("D.M.YYYY"), invoice_period[1].format("D.M.YYYY")
    )

    invoice_data = {}
    invoice_data["address"] = contract.get("address", ["", "", ""])
    invoice_data["cid"] = contract["cid"]
    invoice_data["date"] = arrow.now().strftime(settings.delivery_date_format)
    invoice_data["email"] = contract["email"]
    invoice_data["id"] = invoice_id
    invoice_data["items"] = invoice_items
    invoice_data["period"] = invoice_period_string
    invoice_data["total_gross"] = gross
    invoice_data["total_net"] = net
    invoice_data["total_vat"] = vat
    invoice_data["vat"] = settings.vat

    # We have to save the billed items, as we added the invoice number,
    # s.t. these items will not be billed again.
    # We do this as the last step, so we can be sure the rest of the
    # invoice creation worked
    save_billed_items_yaml(settings, billed_items, contract["cid"])

    return invoice_data


def create_billed_invoices(settings, suffix, cid_only=None, force=False):
    """
    Bulk creates invoice yaml files for the customer from the customers billed items.
    """
    if force:
        print("Force create enabled")

    if cid_only:
        print(f"Only creating to {cid_only}")

    contracts = get_contracts(settings, cid_only=cid_only)
    for cid, contract in contracts.items():
        print(f"Creating billed invoice yaml {cid}.{suffix}")
        try:
            invoice_data = generate_billed_invoice(settings, contract, suffix)
        except NoUnbilledItemsFound:
            print(f"No unbilled items found for {cid}")
            continue
        save_invoice_yaml(settings, invoice_data, force)


def save_billed_items_yaml(settings, billed_items, cid):
    """
    Saves the billed items to the billed items file of the customer 
    """
    billed_items_path = settings.billed_items_dir / f"{cid}.yaml"
    with open(billed_items_path, "w") as outfile:
        yaml.dump(billed_items, outfile)


def get_billed_items(settings, cid):
    """
    Returns the billed_items for the given cid. 

    If there are no billed items yet, an empty list is returned.
    """
    billed_items_path = settings.billed_items_dir / f"{cid}.yaml"

    if not billed_items_path.is_file():
        return []
    else:
        with open(billed_items_path) as infile:
            return yaml.safe_load(infile)


def bill_cid_items(settings, contract, year, month):
    """
    Creates billed items for the given month and year. 
    """
    billed_item_key = f"{year}-{month}"
    month_name = arrow.get(billed_item_key).format("MMMM", locale=settings.arrow_locale)
    billed_items = get_billed_items(settings, contract["cid"])
    if any(item["key"] == billed_item_key for item in billed_items):
        print(f"{billed_item_key} already billed for {contract['cid']}")
    else:
        for item in contract["items"]:
            billed_item = {
                "description": f"{item['description']} {month_name} {year}",
                "price": item["price"],
                "quantity": item["quantity"],
                "subtotal": item["price"] * item["quantity"],
                "key": billed_item_key,
                "invoice": None,
            }
            billed_items.append(billed_item)
    return billed_items


def bill_items(settings, year, month, cid_only=None, dry=False):
    """
    Bill all products for all customers (or just one) i.e. mark them to be included 
    in the next invoice to be created.
    """
    if cid_only:
        print(f"Only creating to {cid_only}")

    contracts = get_contracts(settings, year, month, cid_only)
    for cid, contract in contracts.items():
        print(f"Billing items for {cid}.")
        billed_items = bill_cid_items(settings, contract, year, month)
        if not dry:
            save_billed_items_yaml(settings, billed_items, cid)


def send_invoices(settings, year, month, cid_only, force):
    """
    Sends emails with the invoices as attachment.
    """
    mail_template = get_template(settings.invoice_mail_template_file)

    if force:
        print("Force resend enabled")

    for d in settings.invoices_dir.iterdir():
        if cid_only and cid_only != d.name:
            continue
        else:
            print(f"Only sending to {cid_only}")

        customer_invoice_dir = settings.invoices_dir / d
        if customer_invoice_dir.iterdir():
            for filename in customer_invoice_dir.glob("*.yaml"):
                if not filename.name.endswith(f"{year}.{month:02}.yaml"):
                    continue

                with open(customer_invoice_dir / filename) as yaml_file:
                    invoice_data = yaml.safe_load(yaml_file)

                # don't send invoices multiple times
                if invoice_data.get("sent") and not force:
                    print(f"Skip previously sent invoice {invoice_data['id']}")
                    continue

                invoice_pdf_filename = (
                    f"{settings.company} {filename.with_suffix('.pdf').name}"
                )
                invoice_pdf_path = customer_invoice_dir / filename.with_suffix(".pdf")
                invoice_mail_text = mail_template.render(invoice=invoice_data)

                invoice_email = generate_email(
                    settings,
                    invoice_data["email"],
                    f"{settings.invoice_mail_subject} {invoice_data['id']}",
                    invoice_mail_text,
                    [(invoice_pdf_path, invoice_pdf_filename)],
                )

                print(f"Sending invoice {invoice_data['id']}")

                if send_email(
                    invoice_email,
                    settings.server,
                    settings.username,
                    settings.password,
                    settings.insecure,
                ):
                    with open(customer_invoice_dir / filename, "w") as yaml_file:
                        invoice_data["sent"] = True
                        yaml_file.write(yaml.dump(invoice_data))
