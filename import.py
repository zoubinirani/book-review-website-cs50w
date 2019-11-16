import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    
    #drop tables if they exist
    db.execute("""DROP TABLE IF EXISTS users CASCADE;""")
    db.execute("""DROP TABLE IF EXISTS books CASCADE;""")
    db.execute("""DROP TABLE IF EXISTS reviews CASCADE;""")

    # create users table
    db.execute("""CREATE TABLE users (
        id VARCHAR PRIMARY KEY,
        password VARCHAR NOT NULL
    );""")
        
    # create books table
    db.execute("""CREATE TABLE books (
        isbn VARCHAR PRIMARY KEY,
        title VARCHAR NOT NULL,
        author VARCHAR NOT NULL,
        year VARCHAR NOT NULL
    );""")

    #create reviews table
    db.execute("""CREATE TABLE reviews (
        id SERIAL PRIMARY KEY,
        review VARCHAR NOT NULL,
        isbn VARCHAR NOT NULL,
        user_id VARCHAR NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (isbn) REFERENCES books(isbn)
    );""")
        
    # read in books
    f = open('books.csv')
    reader = csv.reader(f)
    next(reader, None) # skip header
    for isbn, title, author, year in reader:
        db.execute("""INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)""", 
        {"isbn":isbn, "title":title, "author":author, "year":year})
        print(f"Added {title} by {author})")
    db.commit()

if __name__ == "__main__":
    main()
