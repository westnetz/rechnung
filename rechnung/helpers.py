import yaml
import smtplib
import ssl

from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate


def get_template(template_filename):
    """
    Takes the path to the jinja2 template and returns a jinja2 Template instance
    with the contents of the file.

    Args:
        template_filename (str): full path to the template file (jinja2)

    Returns:
        Template: jinja2 Template instance.
    """
    with open(template_filename) as template_file:
        return Template(template_file.read())


def send_email(msg, server, username, password, insecure=True):
    """
    Sends the email.

    Args:
        msg (email.MIMEMultipart): The email to be sent.
    """
    conn = smtplib.SMTP(server, 587)
    context = ssl.create_default_context() if not insecure else None
    conn.starttls(context=context)
    conn.login(username, password)
    conn.send_message(msg)
    conn.quit()


def generate_email_with_pdf_attachment(
    mail_to, mail_from, mail_subject, mail_text, pdf_document, attachment_filename
):
    """
    Sends the invoice to the recipient.

    Args:
        invoice_mail_text (str): Text for the email body
        invoice_pdf (bytes): Invoice PDF
        invoice_data (dict): Invoice Metadata object

    Returns:
        email.MIMEMultipart: Invoice email message object

    """

    msg = MIMEMultipart()
    msg["Subject"] = mail_subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(mail_text, "plain"))

    payload = MIMEBase("application", "pdf")
    payload.set_payload(pdf_document)
    payload.add_header(
        "Content-Disposition", "attachment", filename=attachment_filename
    )

    encoders.encode_base64(payload)

    msg.attach(payload)

    return msg


def get_pdf(filename):
    """
    Reads a pdf file and returns its contents.

    Args:
        invoice_path (str) full path to the invoice file.
    """
    with open(filename, "rb") as infile:
        return infile.read()


def generate_pdf(html_data, css_data, path):
    """
    Takes rendered HTML template and filename and converts it to a PDF invoice
    using weasyprint.

    Args:
        rendered (str): Rendered invoice HTML
        invoice_path: Complete path where the invoice will be written to
    """
    font_config = FontConfiguration()
    html = HTML(string=html_data)
    css = CSS(css_data)
    html.write_pdf(path, stylesheets=[css], font_config=font_config)


def generate_yaml(object, filename):
    """
    Small wrapper around the yaml dump function.

    Args:
        object: Python object to be stored.
        filename: Filename of the yaml file.
    """
    with open(filename, "w") as outfile:
        yaml.dump(object, outfile, default_flow_style=False)


def read_with_default(prompt, default=None):
    """
    Prompts the user to enter some value. If a default value is given,
    the function will return that value, if the user presses enter,
    or enters only characters which are stripped by strip().

    Args:

        prompt: The prompt to be displayed to the user.

        default: The default value to be returned if user enters nothing
                 default: None

    Returns:

        str(): the default if set, empty string if not default and no input,
               the input if something was entered.
    """

    if default:
        full_prompt = "{} [{}]: ".format(prompt, default)
    else:
        full_prompt = "{}: ".format(prompt)

    result = input(full_prompt).strip()

    if not result and not default:
        return str()
    elif not result and default:
        return default
    else:
        return result


def str2bool(var):
    if isinstance(var, bool):
        return var
    else:
        return var.lower() in ["true", "yes"]


def exit_on_miss(key, key_name, required_keys):
    """
    Checks existence of the given key in the given list. If the key is not
    found in the list, an error message is displayed, and the program is
    exited with exit code 1.

    Args:
        key: the key to be found
        key_name: a verbose name of the key, e.g. the variable name
        required_keys: the list where the key is to be found
    """
    if key not in required_keys:
        print("{} must be one of {}".format(key_name, ", ".join(required_keys)))
        exit(1)
