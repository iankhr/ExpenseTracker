# ExpenseTracker
The idea of this progrma is to run a local offline tracker of the expenses. Right now the expenses from SEB and ICA banken are supported.
The program uses your previous expenses to build a database of keywords. Then it uses these keywords to categorise future expenses. 
When new expense (keyword) is found, the program will ask for user input and will ask to classify the expense according to user determined categories

# Installation

1) You will need to install MySQL database and create user credentials for the program to login
2) Use "expenses.sql" file to set-up a schema
3) You will need to manually add different categories to the database. Add them to "categories" table(!)
4) Create folder /Import in the root. This is where sheets with transactions should be uploaded. IMPORTANT: these files are deleted after they were uploaded to the program
5) Install python 3 with pandas, numpy and mysql.connector (Flask is needed to run server.py)
6) Run main.py 


# Files and folders

main.py - is the main pythin file which reads, clssifies and summarizes the expenses
expenses.sql - is the mysql schema for the local database to store expenses
server.py - is the flask application, which for now does nothing; but should allow more interactive work with expenses
info.creds - is the file with credentials to use to login to mysql database (use example_info.creds to create yours)
localdb.py - is the file that connects to database and that write, reads and alters the database

/Import - folder to upload your expenses
/templates - folder for html templates for Flask application

# Help and support
Any help and support are very welcome! In particular with Flask application as well as with adding ability to read expenses from other accounts.
