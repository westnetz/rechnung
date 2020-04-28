import smtplib
import ssl
import yaml
from pathlib import Path

from email.header import Header
from email.message import EmailMessage
from email.utils import formatdate
import mimetypes
from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration


def get_template(template_filename):
    """
    Takes the path to the jinja2 template and returns a jinja2 Template instance
    with the contents of the file.

    Args:
        template_filename (str): full path to the template file (jinja2)

    Returns:
        Template: jinja2 Template instance.
    """

    return Template(Path(template_filename).read_text("utf-8"))


def send_email(msg, server, username, password, insecure=True):
    """
    Sends the email.

    Args:
        msg (email.MIMEMultipart): The email to be sent.
    """
    try:
        conn = smtplib.SMTP(server, 587)
        context = ssl.create_default_context() if not insecure else None
        conn.starttls(context=context)
        conn.login(username, password)
        conn.send_message(msg)
        conn.quit()
        return True
    except Exception as e:
        print(e)


def generate_email(
    settings, mail_to: str, mail_subject: str, mail_text: str, files=None
):
    """
    Generate EmailMessage

    Args:
        settings
        mail_to: receiver mail address
        mail_subject: mail subject
        mail_text: mail text
        files (touple): list of file_path and file_name

    Returns:
        email.EmailMessage

    """
    msg = EmailMessage()
    msg["To"] = Header(mail_to, "utf-8")
    msg["Bcc"] = Header(settings.sender, "utf-8")
    msg["Subject"] = mail_subject
    msg["From"] = settings.sender
    msg["Date"] = formatdate(localtime=True)

    msg.set_content(mail_text)

    for file_path, file_name in files:
        ctype, encoding = mimetypes.guess_type(file_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(file_path, "rb") as fp:
            msg.add_attachment(
                fp.read(), maintype=maintype, subtype=subtype, filename=file_name
            )

    with open("outgoing.msg", "wb") as email_file:
        email_file.write(bytes(msg))

    return msg


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
    css = CSS(css_data, font_config=font_config)
    html.write_pdf(
        path, stylesheets=[css], font_config=font_config, presentational_hints=True
    )


def generate_yaml(object, filename):
    """
    Small wrapper around the yaml dump function.

    Args:
        object: Python object to be stored.
        filename: Filename of the yaml file.
    """
    with open(filename, "w") as outfile:
        yaml.dump(object, outfile, default_flow_style=False, allow_unicode=True)


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
