#!/usr/bin/env python3
import arrow
import csv
import locale
import yaml

from dataclasses import dataclass, asdict
from decimal import Decimal
from pathlib import Path


@dataclass
class Entry:
    date: arrow.Arrow
    subject: str
    amount: Decimal
    sender: str
    receiver: str
    cid: str = ""


class PostBankCsvParser:

    expected_header = [
        "Buchungsdatum",
        "Wertstellung",
        "Umsatzart",
        "Buchungsdetails",
        "Auftraggeber",
        "Empfänger",
        "Betrag (\x80)",
        "Saldo (\x80)",
    ]

    def __init__(self, q):
        self.q = q

    def header_ok(self, header):
        if header != self.expected_header:
            return False
        return True

    def amount_to_decimal(self, value):
        value = value.replace("\x80", "")
        return Decimal.from_float(locale.atof(value)).quantize(Decimal(self.q))

    def sanitize_subject(self, subject):
        return subject.replace("Referenz NOTPROVIDED", "").replace(
            "Verwendungszweck", ""
        )

    def get_entry(self, row):
        return Entry(
            date=arrow.get(row[0], "DD.MM.YYYY"),
            sender=row[4],
            receiver=row[5],
            subject=self.sanitize_subject(row[3]),
            amount=self.amount_to_decimal(row[6]),
        )


class CsvHeaderError(Exception):
    pass


class Entries:
    def __init__(self, entries=None):
        if not entries:
            self.entries = []
        else:
            self.entries = entries

    @classmethod
    def from_csv(cls, csv_file, parser):
        entries = []
        with open(csv_file, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=";", quotechar='"')
            for r, row in enumerate(reader):
                if r == 0:
                    if parser.header_ok(row):
                        continue
                    else:
                        raise CsvHeaderError(
                            f"expected {parser.expected_header} but got {row}"
                        )
                entries.append(parser.get_entry(row))
        return cls(entries)

    def to_yaml(self):
        return yaml.dump(list(map(asdict, self.entries)))


def import_bank_statement_from_file(bank_statement_file, settings):
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    e = Entries.from_csv(
        bank_statement_file, PostBankCsvParser(settings.decimal_quantization)
    )
    outfilename = Path(settings.payments_dir).joinpath(
        f"{arrow.now().isoformat()}.yaml"
    )
    with open(outfilename, "w") as outfile:
        outfile.write(e.to_yaml())
    return outfilename
