import json
from datetime import datetime
import math
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
import sqlite3

load_dotenv()
client = OpenAI()

def read_json(file: str) -> List[Dict]:
    with open(file, "r") as file:
        return json.load(file)

def days_since(date: str) -> int:
    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return (datetime.now() - date).days


def embed(text: str):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def process_repo(repo, cursor):
    name = repo["name"]
    topics = [topic["name"] for topic in repo.get("topics", [])]
    description = repo.get("description", "")
    languages = [lang["name"] for lang in repo.get("languages", [])]

    name_with_owner = repo["nameWithOwner"]
    embedding = embed(
        f"{name} {' '.join(topics)} {description} {' '.join(languages)}"
    )
    stars_log = math.log(repo["stars"])
    days_since_created = days_since(repo["createdAt"])
    days_since_pushed = days_since(repo["pushedAt"])

    try:
        cursor.execute('''
        INSERT INTO repositories (name_with_owner, embedding, stars_log, days_since_created, days_since_pushed)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            name_with_owner,
            json.dumps(embedding),
            stars_log,
            days_since_created,
            days_since_pushed
        ))
    except sqlite3.IntegrityError:
        print(f"WARNING: Duplicate entry {name_with_owner}")
    except Exception as e:
        print(f"WARNING: Error inserting {name_with_owner}: {str(e)}")


def create_database(name):
    conn = sqlite3.connect(name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        name_with_owner TEXT PRIMARY KEY,
        embedding BLOB,
        stars_log REAL,
        days_since_created INTEGER,
        days_since_pushed INTEGER
    )
    ''')
    conn.commit()
    return conn, cursor

def main():
    print("Running Preprocessor Step #2 and #3")
    print("(1/4) reading step 1 output JSON...")
    input_data = read_json("step_1_out.json")

    print("(2/4) creating database...")
    conn, cursor = create_database("step_3_out.sqlite")

    print("(3/4) processing...")
    for repo in input_data:
        process_repo(repo, cursor)

    print("(4/4) saving db...")
    conn.commit()
    conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
