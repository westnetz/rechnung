import yaml
from pathlib import Path
from collections import namedtuple
from copy import deepcopy
from shutil import copy2

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
    "delivery_date_format": "%d. %B %Y",
    "invoice_css_asset_file": "invoice.css",
    "invoice_mail_template_file": "invoice_mail_template.j2",
    "invoice_template_file": "invoice_template.j2.html",
    "invoices_dir": "invoices",
    "logo_asset_file": "logo.svg",
    "policy_attachment_asset_file": "policy.pdf",
}
possible_settings = set(required_settings + list(optional_settings.keys()))

Settings = namedtuple("Settings", required_settings + list(optional_settings.keys()))


class UnknownSettingError(Exception):
    pass


class RequiredSettingMissingError(Exception):
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

        # Check if all required settings are set in yaml file
        for key in required_settings:
            if key not in set(data.keys()):
                raise RequiredSettingMissingError(
                    f"Setting {key} must be set in settings.yaml!"
                )

        # Check for unknown config options
        if error_on_unknown:
            for key in list(data.keys()):
                if key not in possible_settings:
                    raise UnknownSettingError(
                        f"Setting {key} is unknown, and therefore cannot be configured."
                    )

        # Build settings dict
        settings_data = deepcopy(optional_settings)
        settings_data.update(data)

        # prepend base_path to all _dir and _file settings
        for s_key, s_value in settings_data.items():
            # print(s_key, s_value)
            if s_key.endswith(("_file", "_dir")):
                if s_key.endswith(("_asset_file", "_template_file")):
                    s_value = base_path / settings_data["assets_dir"] / s_value
                else:
                    s_value = base_path.joinpath(s_value)
                settings_data[s_key] = s_value
                if create_non_existing_dirs and s_key.endswith("_dir"):
                    if not s_value.is_dir():
                        s_value.mkdir()

        return Settings(**settings_data)


def copy_assets(target_dir, orig_dir=od):
    """
    Copy the original assets, which are shipped with the tool,
    from the original directory (where the tool is installed)
    to the cwd (where the data is stored).
    """
    for asset in orig_dir.glob("*"):
        copy2(orig_dir / asset.name, target_dir / asset.name)
