rechnung - design document
==========================

This document describes the design thoughts and specification of *rechnung* - a command line based contract and invoice management. 

The state of the tool is exclusively stored in files. This distinguishes *rechnung* from other tools on the market (e.g. invoice ninja). Saving all information and state in files has various advantages. It can be tracked with git or any other revision control system. Reverting to a previous state of the tool is not problematic. The user can use his known skills of editing files, to adjust the state, sothe tool can be used in cornercases than we can't even think of. Revision of the data directory should save you from trouble with your local finance authority (depends in which country you are in). 


Workflow
--------

This tool is designed to assist you, if you have the following 
worklow.

You create a new contract for a customer. A contract contains information about the customer, product (and addons), as well as contact information. The contract is sent to the customer by email (using the *send contract* command  and to be signed and returned. 

The contract contains a *product* section. Based on the description the matching product description document from the assets folder is attached to the contracts email as well as the terms and/or returns policy.

The signed contract (as jpg or pdf file) is saved into the *signed\_contracts* directory. After that, the customer can be imported into the system. 

The *initial cost* for the product is appended to the file in the *billed_items* directory.  

Every month (or any other cycle you wish) you run the *bill* command. Every active contract will get all his products appended to his billed items. This way, you keep track of what to put on the next invoice. You can of course manually add positions to the positions file.


If the time is come to send invoices, first you run the *create invoice* command. This will create an invoice with all positions which have not been put on an invoice so far. Also the invoice id is added to the positions for them to not be billed again.

You can now inspect the invoice files. If everything is correct, run the *render-all* command to render all invoices. You can inspect them again and can now use *send invoices* to bulk send the invoices to your customers. 

Now it's time to check your bank account. You can create a match file in the *matchings* directory for every customer to match for the customers IBAN, name, transaction subject, etc. The *annotate* command will annotate a bank statement, i.e. it will try to match a customer for every incoming payment. If there is (only one matching customer) this transaction is added to the customers file in the *saldo* directory, where also all totals of invoices are listed. A saldo file can be created using the *create saldo* command, which can be send to the customer 
to remind them of due payments.
