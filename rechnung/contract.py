import datetime
import locale
import os
import os.path
import yaml

from pathlib import Path
from .config import get_config
from .invoice import get_positions, get_customers
from .settings import ASSETS_DIR
from .helpers import (
    generate_pdf,
    get_pdf,
    get_template,
    generate_email_with_pdf_attachment,
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


def render_pdf_contracts(directory, template, config):
    logo_path = Path(directory) / ASSETS_DIR / "logo.png"

    for contract_filename in Path(config.contracts_dir).glob("*.yaml"):
        contract_pdf_filename = "{}.pdf".format(str(contract_filename).split(".")[0])
        if not Path(contract_pdf_filename).is_file():
            with open(contract_filename) as yaml_file:
                contract_data = yaml.safe_load(yaml_file)
            contract_data["logo_path"] = logo_path

            print("Rendering contract pdf for {}".format(contract_data["cid"]))

            contract_html = template.render(contract=contract_data)

            generate_pdf(contract_html, config.contract_css_filename, contract_pdf_filename)


def save_contract_yaml(contracts_dir, contract_data):
    outfilename = os.path.join(contracts_dir, "{}.yaml".format(contract_data["cid"]))
    try:
        with open(outfilename, "x") as outfile:
            outfile.write(
                yaml.dump(contract_data, default_flow_style=False)
            )
    except FileExistsError:
        print("Contract {} already exists.".format(outfilename))


def create_yaml_contracts(contracts_dir, customers, positions):
     for cid in customers.keys():
         print("Creating contract yaml for {}".format(cid))
         contract_data = generate_contract(
             customers[cid], positions[cid]
         )
         save_contract_yaml(contracts_dir, contract_data)


def send_contract_mail(config, mail_template, cid):
    if not Path(config.contracts_dir).joinpath("{}.pdf").is_file():
        print(f"Contract {cid} not found")

#                 if not filename.endswith(".yaml"):
#                     continue
# 
#                 file_suffix = ".".join(filename.split(".")[-3:-1])
# 
#                 if file_suffix != year_suffix:
#                     continue
# 
#                 with open(os.path.join(customer_invoice_dir, filename)) as yaml_file:
#                     invoice_data, invoice_positions = yaml.load(
#                         yaml_file, Loader=yaml.FullLoader
#                     )
# 
#                 if invoice_data["email"] is None:
#                     continue
# 
#                 invoice_pdf_path = os.path.join(
#                     customer_invoice_dir, "{}.pdf".format(filename[:-5])
#                 )
#                 invoice_pdf_filename = "Westnetz_Rechnung_{}.pdf".format(filename[:-5])
#                 invoice_mail_text = mail_template.render(invoice=invoice_data)
#                 invoice_pdf = get_pdf(invoice_pdf_path)
# 
#                 invoice_receiver = invoice_data["email"]
# 
#                 invoice_email = generate_email_with_pdf_attachment(
#                     invoice_receiver,
#                     config.sender,
#                     config.invoice_mail_subject,
#                     invoice_mail_text,
#                     invoice_pdf,
#                     invoice_pdf_filename,
#                 )
# 
#                 print("Sending invoice {}".format(invoice_data["id"]))
# 
#                 send_email(
#                     invoice_email,
#                     config.server,
#                     config.username,
#                     config.password,
#                     config.insecure,
#                 )

def create_contracts(directory):
    config = get_config(directory)
    customers = get_customers(config.customers_dir)
    positions = get_positions(config.positions_dir)
    create_yaml_contracts(
        config.contracts_dir,
        customers,
        positions,
    )


def render_contracts(directory):
    config = get_config(directory)
    template = get_template(config.contract_template_filename)
    render_pdf_contracts(directory, template, config)


def send_contract(directory, cid):
    config = get_config(directory)
    mail_template = get_template(config.contract_mail_template_filename)
    send_contract_mail(config, mail_template, cid)
