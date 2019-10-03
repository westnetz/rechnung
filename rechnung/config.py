import os
import os.path
import locale
import yaml
import rechnung.settings as settings

from dataclasses import dataclass


@dataclass
class Config:
    assets_dir: str
    company: dict
    contract_css_filename: str
    contract_mail_subject: str
    contract_mail_template_filename: str
    contract_template_filename: str
    contracts_dir: str
    customers_dir: str
    delivery_date_format: str
    insecure: bool
    invoice_css_filename: str
    invoice_mail_subject: str
    invoice_mail_template_filename: str
    invoice_template_filename: str
    invoices_dir: str
    locale: str
    password: str
    policy_attachment_filename: str
    positions_dir: str
    sender: str
    server: str
    username: str
    vat: int


def get_config(directory, config_filename=settings.CONFIG_FILENAME, verify_paths=True):
    """
    This is the main configuration handling function. It performs existence
    checks as well as various content aware checks of its contents. Finally,
    it returns an instance of the Config class.
    """

    config_path = os.path.join(directory, config_filename)
    if not os.path.isfile(config_path):
        raise ValueError("Configfile not found at {}".format(config_path))

    with open(config_path) as config_file:
        config_data = yaml.load(config_file.read(), Loader=yaml.FullLoader)

    config_data["assets_dir"] = os.path.join(directory, settings.ASSETS_DIR)
    config_data["customers_dir"] = os.path.join(directory, settings.CUSTOMERS_DIR)
    config_data["positions_dir"] = os.path.join(directory, settings.POSITIONS_DIR)
    config_data["invoices_dir"] = os.path.join(directory, settings.INVOICES_DIR)
    config_data["contracts_dir"] = os.path.join(directory, settings.CONTRACTS_DIR)
    config_data["invoice_template_filename"] = os.path.join(
        directory, settings.INVOICE_TEMPLATE_FILENAME
    )
    config_data["invoice_css_filename"] = os.path.join(
        directory, settings.INVOICE_CSS_FILENAME
    )
    config_data["invoice_mail_template_filename"] = os.path.join(
        directory, settings.INVOICE_MAIL_TEMPLATE_FILENAME
    )
    config_data["contract_template_filename"] = os.path.join(
        directory, settings.CONTRACT_TEMPLATE_FILENAME
    )
    config_data["contract_css_filename"] = os.path.join(
        directory, settings.CONTRACT_CSS_FILENAME
    )
    config_data["contract_mail_template_filename"] = os.path.join(
        directory, settings.CONTRACT_MAIL_TEMPLATE_FILENAME
    )

    config_data["policy_attachment_filename"] = os.path.join(
        directory, settings.ASSETS_DIR, settings.POLICY_FILENAME
    )

    if verify_paths:
        for key, value in config_data.items():
            if key.endswith("_dir"):
                if not os.path.isdir(value):
                    raise ValueError(
                        "The specified {}: "
                        "'{}' is not a directory.".format(key, value)
                    )
            elif key.endswith("_file") or key.endswith("_filename"):
                if not os.path.isfile(value):
                    raise ValueError(
                        "The specified {}: " "{} is not a file.".format(key, value)
                    )
            else:
                pass

    config = Config(**config_data)
    locale.setlocale(locale.LC_ALL, config.locale)

    return config
