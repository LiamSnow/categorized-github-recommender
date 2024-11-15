import json
from datetime import datetime
import math
from dotenv import load_dotenv
from typing import List, Dict
import sqlite3

def read_db(name):
    input_conn = sqlite3.connect(name)
    input_cursor = input_conn.cursor()
    input_cursor.execute("SELECT name_with_owner, name, description, topics, languages FROM repositories")
    rows = input_cursor.fetchall()
    input_conn.close()
    return rows

def create_db(name):
    conn = sqlite3.connect(name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        name_with_owner TEXT PRIMARY KEY,
        embedding BLOB
    )
    ''')
    conn.commit()
    return conn, cursor

def embed(text: str):
    # TODO embed with 50-100 dimensions
    return

def process_repo(repo, cursor):
    (name_with_owner, name, description, topics, languages) = repo
    embedding_text = f"{name} {description} {topics} {languages}"
    embedding = embed(embedding_text)
    try:
        cursor.execute('''
        INSERT INTO repositories (name_with_owner, embedding)
        VALUES (?, ?)
        ''', (
            name_with_owner,
            json.dumps(embedding),
        ))
    except sqlite3.IntegrityError:
        print(f"WARNING: Duplicate entry {name_with_owner}")
    except Exception as e:
        print(f"WARNING: Error inserting {name_with_owner}: {str(e)}")


def main():
    print("Running Preprocessor Step #2")
    print("(1/4) reading step 1 output db...")
    repos = read_db("step_1_out.sqlite")

    print("(2/4) creating database...")
    conn, cursor = create_db("step_2_out.sqlite")

    print("(3/4) processing...")
    for repo in repos:
        process_repo(repo, cursor)

    print("(4/4) saving db...")
    conn.commit()
    conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
