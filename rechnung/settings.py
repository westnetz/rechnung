import yaml
from pathlib import Path
from collections import namedtuple
from copy import deepcopy
from shutil import copy2
import locale

# File where user settings are read from
SETTINGS_FILE = "settings.yaml"

# Directory in the program directory (pd) where default assets/templates are stored
ORIG_DIR = "orig"

pd = Path(__file__).parent.resolve()
od = pd / ORIG_DIR

# required settings need to be set in the settings.yaml
# optional settings have a default configured in the
# programm which can be overwritten by the user if set
# in the settings.yaml
required_settings = [
    "company",
    "company_address",
    "company_bank",
    "contract_mail_subject",
    "insecure",
    "locale",
    "password",
    "sender",
    "server",
    "username",
    "vat",
]
optional_settings = {
    "invoice_mail_subject": "Rechnung",
    "assets_dir": "assets",
    "contract_css_asset_file": "contract.css",
    "contract_mail_template_file": "contract_mail_template.j2",
    "contract_template_file": "contract_template.j2.html",
    "contracts_dir": "contracts",
    "csv_dir": "csv",
    "delivery_date_format": "%d. %B %Y",
    "invoice_css_asset_file": "invoice.css",
    "invoice_mail_template_file": "invoice_mail_template.j2",
    "invoice_template_file": "invoice_template.j2.html",
    "invoices_dir": "invoices",
    "logo_asset_file": "logo.svg",
    "policy_attachment_asset_file": "policy.pdf",
    "bank_statements_dir": "bank_statements",
    "payments_dir": "payments",
    "decimal_quantization": ".01",
    "billed_items_dir": "billed_items",
    "arrow_locale": "de",
}
possible_settings = set(required_settings + list(optional_settings.keys()))

Settings = namedtuple("Settings", required_settings + list(optional_settings.keys()))


class UnknownSettingError(Exception):
    """
    If a setting is found in the settings.yaml file which is unknown to rechnung, this exception is thrown.
    """

    pass


class RequiredSettingMissingError(Exception):
    """
    If a setting is missing, but required to be set in the settings.yaml, this exception is thrown.
    """

    pass


def create_required_settings_file(cwd, settings_file=SETTINGS_FILE):
    """
    Creates a settings file with all required settings listed, to
    be filled by the user accordingly.
    """
    settings_path = Path(cwd) / settings_file
    if settings_path.exists():
        raise FileExistsError("Settings file already exists.")
    with open(settings_path, "w") as s_file:
        yaml.dump(dict.fromkeys(required_settings), s_file)
    return settings_path


def get_settings_from_cwd(
    cwd, create_non_existing_dirs=False, settings_file=SETTINGS_FILE
):
    """
    Wrapper for get_settings_from_file to allow for easier exchange later.
    """
    return get_settings_from_file(
        Path(cwd) / settings_file, create_non_existing_dirs=create_non_existing_dirs
    )


def check_required_settings(settings, required_settings):
    """
    Check if all required settings are set.
    """
    for key in required_settings:
        if key not in set(settings.keys()):
            raise RequiredSettingMissingError(
                f"Setting {key} must be set in settings.yaml!"
            )


def check_unknown_settings(settings, possible_settings):
    """
    Check for unknown config options.
    """
    for key in list(settings.keys()):
        if key not in possible_settings:
            raise UnknownSettingError(
                f"Setting {key} is unknown, and therefore cannot be configured."
            )


def get_settings_from_file(
    settings_path,
    error_on_unknown=True,
    prepend_base_path=True,
    create_non_existing_dirs=False,
):
    """
    Opens a settings.yaml and returns its contents as
    a namedtuple "Settings". It checks if all required
    settings are found in the settings file, as well
    if there are any unknown settings given.
    Finally the base_path is prepended to all settings
    ending with "_file" or "_dir".
    """
    base_path = settings_path.parent.resolve()
    with open(settings_path) as infile:
        data = yaml.safe_load(infile)

        check_required_settings(data, required_settings)
        if error_on_unknown:
            check_unknown_settings(data, possible_settings)

        # Build settings dict
        settings_data = deepcopy(optional_settings)
        settings_data.update(data)

        # prepend base_path to all _dir and _file settings
        for s_key, s_value in settings_data.items():
            if s_key.endswith(("_file", "_dir")):
                if s_key.endswith(("_asset_file", "_template_file")):
                    s_value = base_path / settings_data["assets_dir"] / s_value
                else:
                    s_value = base_path.joinpath(s_value)
                settings_data[s_key] = s_value
                if create_non_existing_dirs and s_key.endswith("_dir"):
                    if not s_value.is_dir():
                        s_value.mkdir()

        locale.setlocale(locale.LC_ALL, settings_data["locale"])

        return Settings(**settings_data)


def copy_assets(target_dir, orig_dir=od):
    """
    Copy the original assets, which are shipped with the tool,
    from the original directory (where the tool is installed)
    to the cwd (where the data is stored).
    """
    for asset in orig_dir.glob("*"):
        copy2(orig_dir / asset.name, target_dir / asset.name)
