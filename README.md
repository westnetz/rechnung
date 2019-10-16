# rechnung

**rechnung** is a command line based invoice generation system.

![westnetz and reudnetz logos](assets/westnetz_reudnetz.png?raw=true "westnetz and reudnetz")

## Features

* purely file based (no database)
* customizeable (invoice layout is HTML/CSS)

## Installation

Clone this repository to your machine:

```
$ git clone https://github.com/westnetz/rechnung
```

Install the package

```
$ make install
```

**Note:** At the moment installation via pip only works, if you provide the -e option. Therefore it is recommended to use the provided *make install* method.

## Getting Started

This section is a quick walkthrough all the features.

### Initialization

Before you can start generating your own invoices you need to setup your working directory for *rechnung*. By invoking

```
$ rechnung init
```

all required directory and configuration files will be placed in the current working directory. It is recommended to do this in a clean directory.

### Configuration and Customization

You can now edit the *rechnung.config.yaml* file to your needs. You need to enter the credentials for the mail server if you want to send out your invoices by email.

Customization of the invoices can be done by editing the invoice template *templates/invoice_template.j2.html* and the corresponding stylesheet in *assets/inovice.css*. 

### Invoice Creation

After creating your customers, you can create your first invoices. 
The following command

```
$ rechnung create 01.01.2019 31.03.2019 3 2019 Q1
```

will create invoices for all customers for the period from Jan 1st 2019 to Mar 31 2019 which is 3 months in the year 2019 and the suffix Q1. 

Of course the amount of months and the year could be parsed from the given dates, but we found it more failsafe if they are explicitly given.

This step will generate the invoice yaml files. These files are meant to be imported into your bookkeeping system. You can inspect them and even adjust/correct them if you spot errors.

### PDF Creation

If everything is correct, you are ready to create your pdf invoice documents.

```
$ rechnung render
```

This command will render all invoice yaml files, which have no corresponding pdf file. I.e. if you happen to spot an error in an invoice pdf. Simply delete the pdf file, correct the mistake in the invoice yaml, and run the command again.

### Invoice Delivery

If you want to use the included mail delivery service, you should customize the invoice mail template to your needs: *templates/invoice_mail_template.j2*. 

After doing that, you can send all the invoices you just created to your customers:

```
$ rechnung send 2019 09
```

This command will send all invoices with the given suffix to the customer given 
in the invoice yaml file. 

And that's it!

## Copyright

F. Rämisch, 2019
Paul Spooren, 2019

## License

GNU General Public License v3
