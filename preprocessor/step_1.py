import json
import sqlite3
from typing import List, Dict
from datetime import datetime

min_stars = 500
source_json = "data/repo_metadata.json"
dest_db = "data/step_1_out.sqlite"

def read_json(file: str) -> List[Dict]:
    with open(file, 'r') as file:
        return json.load(file)

def meets_requirements(repo: Dict) -> bool:
    return repo['stars'] > min_stars and not repo['isArchived']

def days_since(date: str) -> int:
    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return (datetime.now() - date).days

def save_repo(cursor, repo):
    name_with_owner = repo['nameWithOwner']
    topics = ', '.join([topic["name"] for topic in repo.get("topics", [])])
    languages = ', '.join([lang["name"] for lang in repo.get("languages", [])[:3]])

    try:
        cursor.execute('''
        INSERT INTO repositories (name_with_owner, name, description, topics, languages, stars, days_since_created, days_since_pushed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name_with_owner,
            repo['name'],
            repo['description'],
            topics,
            languages,
            repo['stars'],
            days_since(repo["createdAt"]),
            days_since(repo["pushedAt"])
        ))
    except sqlite3.IntegrityError:
        print(f"WARNING: Duplicate entry {name_with_owner}")
    except Exception as e:
        print(f"WARNING: Error inserting {name_with_owner}: {str(e)}")

def create_db(name):
    conn = sqlite3.connect(name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        name_with_owner TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        topics TEXT,
        languages TEXT,
        stars INTEGER,
        days_since_created INTEGER,
        days_since_pushed INTEGER
    )
    ''')
    conn.commit()
    return conn, cursor

if __name__ == "__main__":
    print("Step #1 - Filter Repos and Save Relevant Data into SQLite DB")
    print(f"(1/4) reading {source_json} this will take awhile...")
    repos = read_json(source_json)

    print(f"(2/4) making {dest_db}...")
    conn, cursor = create_db(dest_db)

    print("(3/4) filtering...")
    count = 0
    for repo in repos:
        if meets_requirements(repo):
            save_repo(cursor, repo)
            count += 1

    print(f" -> filtered down to {count} repos")

    print(f"(4/4) saving {dest_db}...")
    conn.commit()
    conn.close()

    print("Done!")
    print("please wait for deallocation...")
