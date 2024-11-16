from dotenv import load_dotenv
import sqlite3
from openai import OpenAI
from sklearn.decomposition import PCA
import numpy as np
import json

# load_dotenv()
# client = OpenAI()

def read_db(name):
    input_conn = sqlite3.connect(name)
    input_cursor = input_conn.cursor()
    input_cursor.execute("SELECT name_with_owner, name, description, topics, languages FROM repositories")
    rows = input_cursor.fetchall()
    input_conn.close()
    return rows

def make_openai_req(repo):
    (name_with_owner, name, description, topics, languages) = repo
    embedding_text = f"{name} {description} {topics} {languages}"
    return json.dumps({
        "custom_id": name_with_owner,
        "method": "POST",
        "url": "/v1/embeddings",
        "body": {
            "model": "text-embedding-3-small",
            "input": embedding_text
        }
    })

def main():
    print("Running Preprocessor Step #2")
    print("(1/X) reading step 1 output db...")
    repos = read_db("step_1_out.sqlite")

    print("(2/X) making OpenAI batch file...")
    with open("step_2_batch.jsonl", "w") as batch_file:
        for repo in repos:
            req = make_openai_req(repo)
            batch_file.write(req + "\n")

    print("Done!")

if __name__ == "__main__":
    main()
