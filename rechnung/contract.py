import datetime
import locale
import os
import os.path
import yaml

from pathlib import Path
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
    generate_email_with_pdf_attachments,
    send_email,
)


def get_contracts(settings):
    contracts = {}
    for filename in settings.contracts_dir.glob("*.yaml"):

        if not filename.endswith(".yaml"):
            continue

        with open(Path(settings.contracts_dir / filename), "r") as contract_file:
            contract = yaml.safe_load(contract_file)

        contracts[contract["cid"]] = contract
    return contracts


def create_contract(customer, positions):
    contract_data = customer
    contract_data["product"] = positions[0]
    contract_data["product"]["price"] = round(positions[0]["price"] * 1.19, 2)

    if "email" not in customer.keys():
        contract_data["email"] = None
    else:
        contract_data["email"] = customer["email"]

    return contract_data


def render_contracts(settings):
    template = get_template(settings.contract_template_file)
    logo_path = settings.assets_dir / "logo.png"

    for contract_filename in Path(settings.contracts_dir).glob("*.yaml"):
        contract_pdf_filename = "{}.pdf".format(str(contract_filename).split(".")[0])
        if not Path(contract_pdf_filename).is_file():

            with open(contract_filename) as yaml_file:
                contract_data = yaml.safe_load(yaml_file)
            print("Rendering contract pdf for {}".format(contract_data["cid"]))
            contract_data["logo_path"] = logo_path

            for item in contract_data["items"]:
                for element in ["price", "initial_cost"]:
                    item[element] = locale.format_string("%.2f", item.get(element, 0))

            if contract_data["start"]:
                try:
                    contract_data["start"] = contract_data["start"].strftime(
                        "%-d. %B %Y"
                    )
                except ValueError:
                    pass

            print(contract_data)
            contract_html = template.render(contract=contract_data)

            generate_pdf(
                contract_html, settings.contract_css_asset_file, contract_pdf_filename
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
        contract_data = create_contract(customers[cid], positions[cid])
        save_contract_yaml(contracts_dir, contract_data)


def send_contract(settings, cid):
    mail_template = get_template(settings.contract_mail_template_file)
    contract_pdf_path = Path(settings.contracts_dir) / f"{cid}.pdf"
    contract_yaml_filename = Path(settings.contracts_dir) / f"{cid}.yaml"

    if not contract_pdf_path.is_file():
        print(f"Contract {cid} not found")

    with open(contract_yaml_filename) as yaml_file:
        contract_data = yaml.safe_load(yaml_file)

        if contract_data["email"] is None:
            print("No email given for contract {cid}")
            quit()

        contract_pdf_filename = f"{settings.company} {contract_yaml_filename.stem}.pdf"
        contract_mail_text = mail_template.render()
        contract_pdf = get_pdf(contract_pdf_path)

        pdf_documents = [contract_pdf]
        pdf_filenames = [contract_pdf_filename]

        for item in contract_data["items"]:
            item_pdf_file = f"{item['description']}.pdf"
            if not item_pdf_file in pdf_filenames:
                item_pdf_path = Path(settings.assets_dir / item_pdf_file)
                if item_pdf_path.is_file():
                    item_pdf = get_pdf(item_pdf_path)
                    pdf_documents.append(item_pdf)
                    pdf_filenames.append(item_pdf_file)
                else:
                    print(f"Item file {item_pdf_file} not found")

        if settings.policy_attachment_asset_file:
            policy_pdf_file = settings.policy_attachment_asset_file
            policy_pdf_path = settings.assets_dir / policy_pdf_file
            if policy_pdf_path.is_file():
                policy_pdf = get_pdf(policy_pdf_path)
                pdf_documents.append(policy_pdf)
                pdf_filenames.append(policy_pdf_file)
            else:
                print(
                    f"Policy file {settings.policy_attachment_asset_file.name} not found"
                )

        contract_email = generate_email_with_pdf_attachments(
            contract_data["email"],
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


def create_contracts(settings):
    positions = get_positions(settings.positions_dir)
    create_yaml_contracts(settings.contracts_dir)
