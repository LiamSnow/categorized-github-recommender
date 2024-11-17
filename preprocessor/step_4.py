from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import random

# Reference: https://platform.openai.com/docs/guides/batch

load_dotenv()
client = OpenAI()

def read_db(name):
    input_conn = sqlite3.connect(name)
    input_cursor = input_conn.cursor()
    input_cursor.execute(
        "SELECT name_with_owner, name, description, topics, languages, cluster FROM repositories"
    )
    rows = input_cursor.fetchall()
    input_conn.close()
    return rows

def prompt_gpt(repos_str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                # TODO number of words should be tweakable (maybe depending on # of clusters?)
                "content": f"Make a category name (4-10 words) for the following GitHub Repositories?\n\nRepositories:\n{repos_str}",
            }
        ],
        temperature=0.3,
        max_tokens=64,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].message.content.replace("\n", "")

def copy_make_db(source_db, dest_db):
    with open(source_db, "rb") as src, open(dest_db, "wb") as dst:
        dst.write(src.read())
    conn = sqlite3.connect(dest_db)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    ''')
    return conn, cursor

def main():
    num_samples = 20

    print("Step #4 - Cluster Labeling (Categorization)")

    print("reading db")
    source_db = "data/step_3_out.sqlite"
    dest_db = "data/final.sqlite"
    repos = read_db(source_db)

    print("copying db")
    conn, cursor = copy_make_db(source_db, dest_db)

    unique_clusters = list(set(repo[5] for repo in repos))  # cluster is at index 5
    print(f"processing {len(unique_clusters)} clusters!")

    for cluster_id in unique_clusters:
        cluster_repos = [repo for repo in repos if repo[5] == cluster_id]
        sample_repos = random.sample(cluster_repos, min(num_samples, len(cluster_repos)))

        repos_str = ""
        for repo in sample_repos:
            name_with_owner, _, description, topics, languages, _ = repo
            repos_str += f"{name_with_owner}: {description} | Topics: {topics} | Languages: {languages}\n"

        # TODO batch request -- Hitting Rate limit
        cluster_name = prompt_gpt(repos_str)
        print(f" . {cluster_id} -> {cluster_name}")
        cursor.execute('''
        INSERT INTO clusters (id, name)
        VALUES (?, ?)
        ''', (cluster_id, cluster_name))
        conn.commit()

    conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
