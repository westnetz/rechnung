import os
import os.path
import subprocess
import rechnung.settings

from shutil import copy2

base_path = os.path.dirname(os.path.abspath(__file__))

DIRECTORIES = ["invoices", "customers", "positions", "templates", "assets"]
FILES = {
    "assets": ["invoice.css", "logo.png"],
    "templates": ["invoice_template.j2.html", "invoice_mail_template.j2"],
}
CONFIG_FILENAME = "rechnung.config.yaml"


def init_dir(directory, without_samples=False):
    """
    Creates directories, copies templates and sample
    configuration to the given directory.
    """

    copy2(
        os.path.join(base_path, "templates", "sample.config.yaml"),
        os.path.join(directory, CONFIG_FILENAME),
    )

    for d in DIRECTORIES:
        if not os.path.isdir(d):
            os.mkdir(os.path.join(directory, d))

    for d, fs in FILES.items():
        for f in fs:
            copy2(os.path.join(base_path, d, f), os.path.join(directory, d, f))

    if not without_samples:

        copy2(
            os.path.join(base_path, "templates", "sample.positions.yaml"),
            os.path.join(directory, "positions", "1000.yaml"),
        )
        copy2(
            os.path.join(base_path, "templates", "sample.customer.yaml"),
            os.path.join(directory, "customers", "1000.yaml"),
        )

def check_dir(directory):
    """
    Check if the tool was initialized properly in the current
    working directory.
    """

    error = 0

    for d in DIRECTORIES:
        if not os.path.isdir(os.path.join(directory, d)):
            print("Missing directory: {}".format(d))
            error = 1

    if not os.path.isfile(os.path.join(directory, CONFIG_FILENAME)):
        print("Missing configuration file: {}".format(CONFIG_FILENAME))
        error = 1
    # Check if directory is tracked with git
    if (
        subprocess.call(
            ["git", "-C", directory, "status"],
            stderr=subprocess.STDOUT,
            stdout=open(os.devnull, "w"),
        )
        != 0
    ):
        print("⚠️ We recommend tracking this directory with git!")

    return error
