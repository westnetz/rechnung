import arrow
import datetime
import locale
import yaml
from collections import OrderedDict

from pathlib import Path
from .helpers import generate_pdf, get_template, generate_email, send_email


def get_contracts(settings, year=None, month=None, cid_only=None, inactive=False):
    """
    Fetches all contracts from the settings.contracts_dir directory.
    Returns a dict with all active contracts, i.e. contracts with started
    in the past.
    """
    contracts = OrderedDict()
    for filename in settings.contracts_dir.glob("*.yaml"):
        if cid_only and cid_only != filename.stem:
            continue

        contract = yaml.safe_load(
            (settings.contracts_dir / filename).read_text("utf-8")
        )

        if year and month:
            requested_date = arrow.get(f"{year}-{month:02}")
            if "end" in contract.keys():
                if arrow.get(contract["end"]) < requested_date:
                    print(f"Ignoring {contract['cid']} with end {contract['end']}")
                    continue
            if arrow.get(contract["start"]) > requested_date:
                print(f"Ignoring {contract['cid']} with start {contract['start']}")
                continue
            contracts[contract["cid"]] = contract
        else:
            contracts[contract["cid"]] = contract

    return {k: contracts[k] for k in sorted(contracts)}


def render_contracts(settings):
    """
    Renders all contracts as pdfs to settings.contracts_dir
    """
    template = get_template(settings.contract_template_file)
    logo_path = settings.assets_dir / "logo.png"

    for contract_filename in Path(settings.contracts_dir).glob("*.yaml"):
        contract_pdf_filename = "{}.pdf".format(str(contract_filename).split(".")[0])
        if not Path(contract_pdf_filename).is_file():
            contract_data = yaml.safe_load(contract_filename.read_text("utf-8"))
            print("Rendering contract pdf for {}".format(contract_data["cid"]))
            contract_data.update(settings._asdict())

            contract_data["price_total"] = locale.format_string(
                "%.2f", sum([item["price"] for item in contract_data["items"]])
            )
            contract_data["initial_total"] = locale.format_string(
                "%.2f", sum([item["initial"] for item in contract_data["items"]])
            )

            if "start" in contract_data.keys():
                contract_data["start"] = arrow.get(contract_data["start"]).format(
                    "DD.MM.YYYY", locale=settings.arrow_locale
                )

            contract_html = template.render(**contract_data)

            generate_pdf(
                contract_html, settings.contract_css_asset_file, contract_pdf_filename
            )


def send_contract(settings, cid):
    """
    Sends the contract specified with the cid via email to the customer.

    If set, the policy and the product description of the main product 
    will be attached.
    """
    mail_template = get_template(settings.contract_mail_template_file)
    contract_pdf_path = Path(settings.contracts_dir) / f"{cid}.pdf"
    contract_yaml_filename = Path(settings.contracts_dir) / f"{cid}.yaml"

    if not contract_pdf_path.is_file():
        print(f"Contract {cid} not found")

    contract_data = yaml.safe_load(contract_yaml_filename.read_text("utf-8"))

    if contract_data["email"] is None:
        print("No email given for contract {cid}")
        quit()

    contract_pdf_filename = (
        f"{settings.company_name} {contract_yaml_filename.stem}.pdf"
    )
    contract_mail_text = mail_template.render()

    attachments = [(contract_pdf_path, contract_pdf_filename)]

    for item in contract_data["items"]:
        item_pdf_file = f"{item['description']}.pdf"
        item_pdf_path = Path(settings.assets_dir / item_pdf_file)
        if item_pdf_path.is_file():
            attachments.append((item_pdf_path, item_pdf_file))
        else:
            print(f"Item file {item_pdf_file} not found")

    if settings.policy_attachment_asset_file:
        policy_pdf_path = settings.policy_attachment_asset_file
        if policy_pdf_path.is_file():
            attachments.append((policy_pdf_path, policy_pdf_path.name))
        else:
            print(f"Missing {settings.policy_attachment_asset_file.name}")

    contract_email = generate_email(
        settings,
        contract_data["email"],
        settings.contract_mail_subject,
        contract_mail_text,
        attachments,
    )

    print("Sending contract {}".format(contract_data["cid"]))

    send_email(
        contract_email,
        settings.server,
        settings.username,
        settings.password,
        settings.insecure,
    )
