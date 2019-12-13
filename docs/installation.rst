Installation
============

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
