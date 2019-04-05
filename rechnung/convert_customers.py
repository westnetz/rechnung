import os
import os.path
import yaml

from .config import get_config


def convert_customers(directory, cdir):
    """
    This reads the config in the given directory and imports customers from
    cdir into the customers directory in the given directory.
    """
    n_converted = 0

    config = get_config(directory)

    for filename in os.listdir(cdir):

        if not filename.endswith(".yaml"):
            print("Not a valid file: {}".format(filename))
            continue

        origin_file = os.path.join(cdir, filename)

        with open(origin_file, "r") as infile:
            data = yaml.load(infile, Loader=yaml.FullLoader)

        # Rewrite id to slug
        if "id" in data.keys():
            data["slug"] = data.pop("id")

        removes = ["paid", "invoices", "rrule", "inactive", "invalidated", "vatid"]

        for remove in removes:
            if remove in data.keys():
                data.pop(remove)

        if "cid" in data.keys():
            data["cid"] = str(data.pop("cid"))

        if "vlan" in data.keys():
            data["vid"] = data.pop("vlan")

        # mobile to phone to string
        if "mobile" in data.keys():
            data["phone"] = str(data.pop("mobile"))

        # phone to string
        if "phone" in data.keys():
            data["phone"] = str(data.pop("phone"))

        # extract invoice positions / products
        if "invoice" in data.keys():
            positions = data.pop("invoice")

            # Adjust for VAT
            for position in positions:
                position["price"] = round(position["price"] / 1.19, 2)

        # address to list
        if "address" in data.keys():
            if isinstance(data["address"], str):
                address = data.pop("address")
                parts = address.split("\n")
                new_address = []
                for part in parts:
                    if len(part) > 0:
                        new_address.append(part)
                data["address"] = new_address

        if "name" not in data.keys():
            data["name"] = data["address"][0]

        target_file = os.path.join(config.customers_dir, "{}.yaml".format(data["cid"]))

        with open(target_file, "w") as outfile:
            yaml.dump(data, outfile, default_flow_style=False)

        p_file = os.path.join(config.positions_dir, "{}.yaml".format(data["cid"]))

        with open(p_file, "w") as outfile:
            yaml.dump(positions, outfile, default_flow_style=False)

        n_converted += 1

    print("Finished.\nConverted {} files.".format(n_converted))
