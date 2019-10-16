import datetime
import locale
import yaml
from collections import OrderedDict

from .helpers import generate_pdf, get_template, generate_email, send_email


def get_contracts(
    settings,
    year: int = None,
    month: int = None,
    cid_only: int = None,
    inactive: bool = False,
    slug: str = None,
):
    """
    Get list of stored contracts

    Args:
        settings (NamedTuple): Currently active settings
        year (int): Contract must be created before that time
        month (int: Combined with year
        cid_only (int): Only return single contract based on argument
        inactive (bool): return also inactive contracts
        slug (str): return only contract based on argument

    Returns:
        OrderedDict: contract IDs are keys and contracts the values
    """
    contracts = OrderedDict()
    for filename in settings.contracts_dir.glob("*.yaml"):
        if cid_only and cid_only != filename.stem:
            continue

        with open(settings.contracts_dir / filename, "r") as contract_file:
            contract = yaml.safe_load(contract_file)

        if slug and slug != contract["slug"]:
            continue

        if year and month:
            if contract["start"] < datetime.date(year, month, 1):
                contracts[contract["cid"]] = contract
            else:
                print(f"Ignoring {contract['cid']} with start {contract['start']}")
        else:
            contracts[contract["cid"]] = contract

    return {k: contracts[k] for k in sorted(contracts)}


def render_contracts(settings):
    template = get_template(settings.contract_template_file)
    logo_path = settings.assets_dir / "logo.png"

    for contract_filename in settings.contracts_dir.glob("*.yaml"):
        contract_pdf_filename = contract_filename.with_suffix(".pdf")
        if not contract_pdf_filename.is_file():

            with open(contract_filename) as yaml_file:
                contract_data = yaml.safe_load(yaml_file)
            print(f"Rendering contract pdf for {contract_data['cid']}")
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

            contract_html = template.render(contract=contract_data)

            generate_pdf(
                contract_html, settings.contract_css_asset_file, contract_pdf_filename
            )


def send_contract(settings, cid):
    mail_template = get_template(settings.contract_mail_template_file)
    contract_pdf_path = settings.contracts_dir / f"{cid}.pdf"
    contract_yaml_filename = settings.contracts_dir / f"{cid}.yaml"

    if not contract_pdf_path.is_file():
        print(f"Contract {cid} not found")

    with open(contract_yaml_filename) as yaml_file:
        contract_data = yaml.safe_load(yaml_file)

        if contract_data["email"] is None:
            print("No email given for contract {cid}")
            quit()

        contract_pdf_filename = f"{settings.company} {contract_yaml_filename.stem}.pdf"
        contract_mail_text = mail_template.render()

        attachments = [(contract_pdf_path, contract_pdf_filename)]

        for item in contract_data["items"]:
            item_pdf_file = f"{item['description']}.pdf"
            item_pdf_path = settings.assets_dir / item_pdf_file
            if item_pdf_path.is_file():
                attachments.append((item_pdf_path, item_pdf_file))
            else:
                print(f"Item file {item_pdf_file} not found")

        if settings.policy_attachment_asset_file:
            policy_pdf_file = settings.policy_attachment_asset_file
            policy_pdf_path = settings.assets_dir / policy_pdf_file
            if policy_pdf_path.is_file():
                attachments.append((policy_pdf_path, policy_pdf_file))
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
