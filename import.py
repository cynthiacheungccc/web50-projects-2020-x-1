import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine("postgres://uwehclrwoyjdaa:41eabd2efcb1dd14c0570d27ff2e465383a7bc35870dd957d43a40c1e1173cec@ec2-50-17-178-87.compute-1.amazonaws.com:5432/dfbl0f5lfpt12k")
db_session = scoped_session(sessionmaker(bind=engine))

def import_books_from_csv(csv_file):
    with open(csv_file, newline='') as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            db_session.execute("INSERT INTO public.book(isbn, title, author, year) VALUES ('{isbn}', E'{title}', E'{author}', '{year}')".format_map({
                "isbn": row[0],
                "title": row[1].replace("'", "\\\'"),
                "author": row[2].replace("'", "\\\'"),
                "year": row[3]
            }))
        db_session.commit()

if __name__ == "__main__":
    import_books_from_csv("books.csv")