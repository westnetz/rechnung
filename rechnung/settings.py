import os.path

CONFIG_FILENAME = "rechnung.config.yaml"
CUSTOMERS_DIR = "customers"
INVOICES_DIR = "invoices"
POSITIONS_DIR = "positions"
CONTRACTS_DIR = "contracts"
TEMPLATES_DIR = "templates"
ASSETS_DIR = "assets"
INVOICE_TEMPLATE_FILENAME = os.path.join(TEMPLATES_DIR, "invoice_template.j2.html")
INVOICE_CSS_FILENAME = os.path.join(ASSETS_DIR, "invoice.css")
INVOICE_MAIL_TEMPLATE_FILENAME = os.path.join(TEMPLATES_DIR, "invoice_mail_template.j2")
CONTRACT_TEMPLATE_FILENAME = os.path.join(TEMPLATES_DIR, "contract_template.j2.html")
CONTRACT_CSS_FILENAME = os.path.join(ASSETS_DIR, "contract.css")
CONTRACT_MAIL_TEMPLATE_FILENAME = os.path.join(
    TEMPLATES_DIR, "contract_mail_template.j2"
)
CONTRACT_REMINDER_TEMPLATE_FILENAME = os.path.join(
    TEMPLATES_DIR, "contract_reminder_template.j2"
)
