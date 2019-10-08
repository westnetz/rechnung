import datetime
import locale
import os
import os.path
import yaml

from pathlib import Path
from .invoice import get_positions, get_customers
from .settings import get_settings_from_cwd
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
    generate_email_with_pdf_attachments,
    send_email,
)


def generate_contract(customer, positions):

    contract_data = customer
    contract_data["product"] = positions[0]
    contract_data["product"]["price"] = round(positions[0]["price"] * 1.19, 2)

    if "email" not in customer.keys():
        contract_data["email"] = None
    else:
        contract_data["email"] = customer["email"]

    return contract_data


def render_pdf_contracts(directory, template, settings):
    logo_path = settings.assets_dir / "logo.png"

    for contract_filename in Path(settings.contracts_dir).glob("*.yaml"):
        contract_pdf_filename = "{}.pdf".format(str(contract_filename).split(".")[0])
        if not Path(contract_pdf_filename).is_file():

            with open(contract_filename) as yaml_file:
                contract_data = yaml.safe_load(yaml_file)
            print("Rendering contract pdf for {}".format(contract_data["cid"]))
            contract_data["logo_path"] = logo_path

            for element in ["price", "initial_cost"]:
                contract_data["product"][element] = locale.format_string(
                    "%.2f", contract_data["product"][element]
                )

            if contract_data["start"]:
                try:
                    contract_data["start"] = datetime.datetime.strptime(
                        contract_data["start"], "%Y-%m-%d"
                    ).strftime("%-d. %B %Y")
                except ValueError:
                    pass

            contract_html = template.render(contract=contract_data)

            generate_pdf(
                contract_html, settings.contract_css_file, contract_pdf_filename
            )


def save_contract_yaml(contracts_dir, contract_data):
    outfilename = os.path.join(contracts_dir, "{}.yaml".format(contract_data["cid"]))
    try:
        with open(outfilename, "x") as outfile:
            outfile.write(yaml.dump(contract_data, default_flow_style=False))
    except FileExistsError:
        print("Contract {} already exists.".format(outfilename))


def create_yaml_contracts(contracts_dir, customers, positions):
    for cid in customers.keys():
        print("Creating contract yaml for {}".format(cid))
        contract_data = generate_contract(customers[cid], positions[cid])
        save_contract_yaml(contracts_dir, contract_data)


def send_contract_mail(settings, mail_template, cid):
    contract_pdf_path = Path(settings.contracts_dir) / f"{cid}.pdf"
    contract_yaml_filename = Path(settings.contracts_dir) / f"{cid}.yaml"

    if not contract_pdf_path.is_file():
        print(f"Contract {cid} not found")

    with open(contract_yaml_filename) as yaml_file:
        contract_data = yaml.safe_load(yaml_file)

        if contract_data["email"] is None:
            print("No email given")

        contract_pdf_filename = "Dein_Westnetz_Vertrag_{}.pdf".format(cid)
        contract_mail_text = mail_template.render()
        contract_pdf = get_pdf(contract_pdf_path)

        product_pdf_file = "{}.pdf".format(contract_data["product"]["description"])
        product_pdf_path = Path(settings.assets_dir) / product_pdf_file
        product_pdf = get_pdf(product_pdf_path)

        policy_pdf_file = settings.policy_attachment_asset_file
        policy_pdf_path = Path(settings.assets_dir) / policy_pdf_file
        policy_pdf = get_pdf(policy_pdf_path)

        pdf_documents = [contract_pdf, product_pdf, policy_pdf]
        pdf_filenames = [
            contract_pdf_filename,
            product_pdf_file,
            "Widerrufsbelehrung.pdf",
        ]

        contract_receiver = contract_data["email"]

        contract_email = generate_email_with_pdf_attachments(
            contract_receiver,
            settings.sender,
            settings.contract_mail_subject,
            contract_mail_text,
            pdf_documents,
            pdf_filenames,
        )

        print("Sending contract {}".format(contract_data["cid"]))

        send_email(
            contract_email,
            settings.server,
            settings.username,
            settings.password,
            settings.insecure,
        )


def create_contracts(directory):
    settings = get_settings_from_cwd(directory)
    customers = get_customers(settings.customers_dir)
    positions = get_positions(settings.positions_dir)
    create_yaml_contracts(settings.contracts_dir, customers, positions)


def render_contracts(directory):
    settings = get_settings_from_cwd(directory)
    template = get_template(settings.contract_template_file)
    render_pdf_contracts(directory, template, settings)


def send_contract(directory, cid):
    settings = get_settings_from_cwd(directory)
    mail_template = get_template(settings.contract_mail_template_file)
    send_contract_mail(settings, mail_template, cid)
