from datetime import datetime
from math import ceil

class base_service(object):

    def __init__(self, db_session):
        if not db_session:
            raise RuntimeError("Database connection session is not set.")
        self.__db_session = db_session

    def execute(self, sql):
        return self.__db_session.execute(sql)

    def commit(self):
        self.__db_session.commit()

class user_service(base_service):
    
    def create_user(self, username, password):
        result = self.execute("INSERT INTO public.account(username, password) VALUES ('{username}', '{password}') RETURNING id".format_map({
            "username": username,
            "password": password
        })).fetchall()
        self.commit()
        if result:
            return result[0][0]
        return None

    def get_user(self, username, password):
        result = self.execute("SELECT id, username FROM public.account WHERE username='{username}' and password='{password}'".format_map({
            "username": username,
            "password": password
        }))
        rows = result.fetchall()
        if rows:
            return {
                "id": rows[0]["id"],
                "username": rows[0]["username"]
            }
        return None

class book_service(base_service):

    def create_book(self, isbn, title, author, year):
        result = self.execute("INSERT INTO public.book(isbn, itle, author, year) VALUES ('{isbn}', '{title}', '{author}', '{year}') RETURNING id".format_map({
            "isbn": isbn,
            "title": title,
            "author": author,
            "year": year
        }))
        self.commit()
        return result.fetchone()[0]

    def count_page_numbers(self, per_page, keyword=None):
        total_count_sql = "SELECT count(id) as total FROM public.book"
        if keyword:
            total_count_sql = """SELECT count(id) as total FROM public.book 
                        WHERE isbn LIKE E'%%{keyword}%%' or title LIKE E'%%{keyword}%%' or author LIKE E'%%{keyword}%%'
                  """.format_map({
                            "keyword": keyword.replace("'", "\\\'")
                        })
        total = self.execute(total_count_sql).scalar()
        total_pages = ceil(total/per_page)
        return total_pages

    def get_books(self, page_num, per_page, keyword=None):
        page_offset = (page_num - 1) * per_page
        sql = 'SELECT * FROM public.book LIMIT {0} OFFSET {1}'.format(per_page, page_offset)
        if keyword:
            sql = """SELECT * FROM public.book 
                        WHERE isbn LIKE E'%%{keyword}%%' or title LIKE E'%%{keyword}%%' or author LIKE E'%%{keyword}%%'
                        LIMIT {per_page} OFFSET {page_offset}
                  """.format_map({
                            "per_page": per_page, 
                            "page_offset": page_offset,
                            "keyword": keyword.replace("'", "\\\'")
                        })
        result = self.execute(sql)
        rows = result.fetchall()
        books = [{
            "id": row["id"],
            "isbn": row["isbn"],
            "title": row["title"],
            "author": row["author"],
            "year": row["year"]
        } for row in rows]
        return books

    def get_book_by_isbn(self, isbn):
        row = self.execute('''
                SELECT * FROM public.book
                WHERE isbn='{isbn}'
                '''.format_map({ "isbn": isbn})
            ).fetchone()
        if not row:
            return None
        book = {
            "id": row["id"],
            "isbn": row["isbn"],
            "title": row["title"],
            "author": row["author"],
            "year": row["year"]
        }
        return book 
    
    def get_book_detail(self, isbn):
        rows = self.execute('''
                SELECT * FROM public.book
                WHERE isbn='{isbn}'
                '''.format_map({ "isbn": isbn})
            ).fetchall()
        
        if not rows:
            return {}
        row = rows[0]
        book = {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "year": int(row["year"]),
            "isbn": row["isbn"]
        }
        results = self.execute('''
            SELECT score FROM public.review
            WHERE book_id={book_id}
            '''.format_map({"book_id": book["id"]})).fetchall()
        reviews = [ row["score"] for row in results]
        book["review_count"] = len(reviews)
        average = sum(reviews) / len(reviews)
        book["average_score"] = float(round(average, 2))
        del book["id"]
        return book

class review_service(base_service):
    
    def create_review(self, user_id, book_id, rating, comment):
        result = self.execute('''
            INSERT INTO public.review (user_id, book_id, score, comment, create_date) 
            VALUES ({user_id}, {book_id}, {score}, '{comment}', '{create_date}')
            RETURNING id
            '''.format_map({
                "user_id": user_id,
                "book_id": book_id,
                "score": rating,
                "comment": comment,
                "create_date": datetime.now().strftime("%Y-%m-%d")
            })
            )
        self.commit()
        return result.fetchone()[0]
    
    def update_review(self, user_id, book_id, rating, comment):
        self.execute('''
            UPDATE public.review 
            SET score='{score}', comment='{comment}'
            WHERE user_id='{user_id}' and book_id='{book_id}'
            '''.format_map({
                "user_id": user_id,
                "book_id": book_id,
                "score": rating,
                "comment": comment
            })
            )
        self.commit()
        return True 

    def check_review(self, user_id, book_id):
        results = self.execute("SELECT id FROM public.review WHERE user_id={0} and book_id={1}".format(user_id, book_id)).fetchall()
        return len(results) > 0

    def get_reviews_by_book(self, book_id):
        rows = self.execute('''
            SELECT * FROM public.review
            WHERE book_id={book_id}
            '''.format_map({"book_id": book_id})).fetchall()
        reviews = [ {
            "id": row["id"],
            "user_id": row["user_id"],
            "book_id": row["book_id"],
            "comment": row["comment"],
            "create_date": row["create_date"],
            "score": row["score"]
        } for row in rows ]
        for review in reviews:
            user = self.execute("SELECT username FROM public.account WHERE id ={user_id}".format_map({
                "user_id": review["user_id"]
            })).fetchone()
            review["user"] = user["username"]
        return reviews
