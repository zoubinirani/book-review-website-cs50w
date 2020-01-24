# Book Review Website for CS50w

This project is a book review website built in Flask (backend). 

To setup the website from scratch, run setup.sh, this will: drop and create new tables on Heroku, import data to Heroku, setup the flask server, and start the flask server locally. 

To use the website, you first need to register, then login, and then search for a book (either by ISBN, author, or tile). The website also has api access (found via: '/api/<isbn>') 

The main application is application.py. Furthermore, the html/css templates can be found in the 'templates' folder. 
