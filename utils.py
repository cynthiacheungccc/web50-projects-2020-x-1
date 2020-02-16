from requests import get 
from os import environ
import sys 

def get_goodreads_review(isbns, api=environ.get("GOODREADS_REVIEW_API", "https://www.goodreads.com/book/review_counts.json"), key=environ.get("GOODREADS_ACCESS_KEY", "X3hwccM74FW5PMao2tK5gg")):
    resp = get(api, params={
        "key": key,
        "isbns": isbns
    })
    resp.raise_for_status()
    results = {}
    for book in resp.json().get("books", []):
        results[book["isbn"]] = book
    return results



