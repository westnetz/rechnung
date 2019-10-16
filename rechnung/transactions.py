import datetime
import locale
import os
import os.path
import yaml
import csv
import re
from dateutil.parser import parse

from pathlib import Path


def parser_gls(csv_path):
    """
    Parses CSV files from the GLS bank
    """
    groups = [
        r"(?P<type>Dauerauftragsbelast|Dauerauftragsgutschr|Überweisungsauftrag|Basislastschrift|Überweisungsgutschr\.)",
        r"(?P<subject>.*)IBAN:\s?(?P<iban>.+) BIC:\s?(?P<bic>.+)",
    ]
    compiled_groups = re.compile("".join(groups))
    transactions = []

    with open(csv_path, encoding="iso-8859-1") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")

        for row in csv_reader:
            match = compiled_groups.match(row[8].replace("\n", ""))
            if match:
                transactions.append(
                    {
                        **match.groupdict(),
                        "date": parse(row[0], dayfirst=True),
                        "sender": row[3],
                        "amount": float(row[11].replace(",", ".")),
                    }
                )
    return transactions


def read_csv_files(settings, year, month):
    """
    Parses CSV files of a specific year/month combo
    """
    transactions = []
    for bank in settings.csv_dir.iterdir():
        csv_path = bank / f"{year}{month:02}.csv"
        if csv_path.is_file():
            if bank.stem == "gls":
                transactions.extend(parser_gls(csv_path))
            else:
                print("Unknown CSV format")

    return transactions
