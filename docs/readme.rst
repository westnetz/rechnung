Installation and Setup
======================

Prerequisites
-------------

*rechnung* is develop under Linux and currently only tested with Linux. If you happen to use it under Windows, Mac, ... please be aware that unexpected behaviour may be observed. 

Except from having Linux as your operating System, **Python 3.7** is required. Unfortunately this is the only Python version currently supported, as one of the dependencies (html5lib-python, does not support Python >3.8) and we make use of dataclasses which is available for Python >3.7. 

User Installation
-----------------

Currently the recommended installation path is via this repository on github.
To start, clone this repository to your machine:

.. code:: zsh

        $ git clone https://github.com/westnetz/rechnung


And install the package using *pip* or the provided *make install* method.

.. code:: zsh
        
        $ make install


Getting Started
===============

This section is a quick walkthrough all the features.

Initialization
--------------

Before you can start generating your own invoices you need to setup your working directory for *rechnung*. By invoking

.. code:: zsh

        $ rechnung init


all required directory and configuration files will be placed in the current working directory. It is recommended to do this in a clean directory.

Configuration and Customization
-------------------------------

You can now edit the *rechnung.config.yaml* file to your needs. You need to enter the credentials for the mail server if you want to send out your invoices by email.

Customization of the invoices can be done by editing the invoice template *templates/invoice_template.j2.html* and the corresponding stylesheet in *assets/inovice.css*. 

Creating invoices
-----------------

After creating your customers, you can create your first invoices. 
The following command

.. code:: zsh

        $ rechnung create-invoices 2019 10
 
will create invoices for all customers who have a contract starting before and ending after october 2019.

You can force overwrite of existing invoices by giving the *--force/-f* option

.. code:: zsh

        $ rechnung create-invoices --force 2019 10
 
Individual invoices can be created by giving a specific customer id (cid)

.. code:: zsh

        $ rechnung create-invoices -c 1000 2019 10


After creating your invoices you can doublecheck for correctness. 

Rendering invoices (create pdf files)
-------------------------------------

If everything is correct, you are ready to create your pdf invoice documents.

.. code:: zsh

        $ rechnung render-all

This command will render all invoice yaml files, which have no corresponding pdf file. I.e. if you happen to spot an error in an invoice pdf. Simply delete the pdf file, correct the mistake in the invoice yaml, and run the command again.

Sending invoices
----------------

If you want to use the included mail delivery service, you should customize the invoice mail template to your needs: *assets/invoice_mail_template.j2*. 

After doing that, you can send all the invoices you just created to your customers:

.. code:: zsh

        $ rechnung send 2019 09


This command will send all invoices with the given suffix to the customer given 
in the invoice yaml file. 

And that's it!
