.. AlexChat documentation master file, created by
   sphinx-quickstart on Wed Nov  9 16:15:13 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.




.. toctree::
   :hidden:

   self

AlexChat Introduction
=====================
AlexChat is decentralized, cross-platform, object oriented intra-network chat application, that uses only the python standard library. It supports both one-to-one chat connections as well as a network-wide "Broadcast" chat mode, with tabbed organization and a clean UI. It uses text-based commands similar to those used in IRC. AlexChat was written by Alex Kursell as a Grade 12 Computer Science final project.


User Guide
==========
AlexChat is so simple, it dosen't need a user guide! Just double-click on the file to run and follow the prompts. It takes only seconds to get started!


Research Sources
================
This project required a lot of research, as I had never used sockets or threading before, nor had I written a program this large before. A few of the most useful sources I used were as follows:

- The bidict class, copied from a StackOverflow answer at http://stackoverflow.com/a/21894086 and used as the AddressBook class with minor modification.
- The CustomNotebook class, copied from a StackOverflow answer at http://stackoverflow.com/a/39459376 and used with minor modification.
- The Python Socket HOWTO at https://docs.python.org/2/howto/sockets.html, with helpful example code and explanation.
- The 'Documenting Your Project Using Sphinx Guide' at https://pythonhosted.org/an_example_pypi_project/sphinx.html
- The entire python3 documentation https://docs.python.org/3.4/
- http://stackoverflow.com


Testing
=======
AlexChat was tested multiple times by many users. While writing it, I used two computers to test its messaging capabilities. In addition, I also had Adam and Nirmal test the program to ensure that it is user friendly.


Bugs/Limitations
================
Due to AlexChat's reliance on the UDP broadcast feature to get all current users connected to the network, username discovery will not work on computers connected to the school wifi network. Users can still chat by entering their partner's IP address.


Module Documentation
====================

.. toctree::
   :titlesonly:
   :maxdepth: 2

   modules


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

