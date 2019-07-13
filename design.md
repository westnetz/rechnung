# rechnung - design document

This document describes the design thoughts and specification
of *rechnung* - a command line based contract and invoicing 
system

The idea is, that the whole state of the tool is in files. 
Files can easily be edited with any editor, so the tool might
be capable of cornercases than we can think of.

As everything can (and should be) revisioned with git, you 
should be able to not have any trouble with your local finance
authority. Furthermore, you should create one *rechnung* workdir
per *calendar year*, to be able to discard this and only this 
information after 10 years.

## Workflow

This tool is designed to assist you, if you have the following 
worklow.

You create a new contract for a customer. A contract contains
information about the customer, product (and addons), as well
as contact information. The contract is sent to the customer
by email (using the *send contract* command  and to be signed 
and returned. 

The signed contract (as jpg or pdf file) is saved into the 
*signed\_contracts* directory. After that, the customer can 
be imported into the system. 

The import step does 3 things. First, the information about the
customer is saved into a file in the *customers* directory.
Information about the selected product and addons is saved
to the *products* directory. The *initial cost* for the 
product is appended to the file in the *positions* directory.  

Every month (or any other cycle you wish) you run the *bill*
command. Every active customer (from the customers directory) 
will get all his products appended to his positions (to be 
billed). This way, you keep track of what to put on the 
next invoice. You can of course manually add positions to 
the positions file.

If the time is come to send invoices, first you run the 
*create invoice* command. This will create an invoice with 
all positions which have not been put on an invoice so far.
Also the invoice id is added to the positions for them to 
not be billed again.

You can now inspect the invoice files. If everything is correct,
run the *render* command to render all invoices. You can 
inspect them again and can now use *send invoices* to bulk send
the invoices to your customers. 

Now it's time to check your bank account. You can create a 
match file in the *matchings* directory for every customer 
to match for the customers IBAN, name, transaction subject, etc.
The *annotate* command will annotate a bank statement, i.e. it
will try to match a customer for every incoming payment. If 
there is (only one matching customer) this transaction is added
to the customers file in the *saldo* directory, where also all
totals of invoices are listed. A saldo file can be created using
the *create saldo* command, which can be send to the customer 
to remind them of due payments.

## Directory structure

directory name     | purpose
-------------------|--------
assets	           | CSS files, product descriptions, terms of service etc.
contracts          | yaml and pdf files of the contracts
customers	   | customer information to appear on the invoice
matchings	   | matchings to be used in the bank statement annotator
positions	   | the billed products which will appear on the next invoice
products           | the products which will be billed every month
signed\_contracts  | signed contracts are stored here. 
saldo		   | every invoice and bank transaction is listed here, to see if the customer pays his invoices. 
bank\_statements   | bank statements to be annotated are save here
templates          | document and mail templates
