import sqlite3
from openai import OpenAI
from sklearn.decomposition import PCA
import numpy as np
import json
import sys
import math
from openai import OpenAI
from dotenv import load_dotenv

# Reference: https://platform.openai.com/docs/guides/batch
# View Batches: https://platform.openai.com/batches

source_db = "data/step_1_out.sqlite"
batch_req_filename = "data/step_2_batch_N.jsonl"
batch_res_filename = "data/step_2_out_N.jsonl"

load_dotenv()
client = OpenAI()

def read_db(name):
    input_conn = sqlite3.connect(name)
    input_cursor = input_conn.cursor()
    input_cursor.execute(
        "SELECT name_with_owner, name, description, topics, languages FROM repositories"
    )
    rows = input_cursor.fetchall()
    input_conn.close()
    return rows


def make_openai_req(repo):
    (name_with_owner, name, description, topics, languages) = repo
    embedding_text = f"{name} {description} {topics} {languages}"
    return json.dumps(
        {
            "custom_id": name_with_owner,
            "method": "POST",
            "url": "/v1/embeddings",
            "body": {"model": "text-embedding-3-small", "input": embedding_text},
        }
    )

def make_batch_file(num, repos):
    with open(batch_req_filename.replace('N', str(num)), "w") as batch_file:
        for repo in repos:
            req = make_openai_req(repo)
            batch_file.write(req + "\n")

def make():
    print("MAKING Batch Files")
    print("(1/3) reading step 1 output db...")
    repos = read_db(source_db)
    print("(2/3) splitting repos...")
    half_length = math.ceil(len(repos) / 2)
    repos_first_half = repos[:half_length]
    repos_second_half = repos[half_length:]
    print("(3/3) making batch files...")
    make_batch_file(1, repos_first_half)
    make_batch_file(2, repos_second_half)
    print("Done!")

def run_batch_file(num):
    print(f"uploading {num}")
    batch_input_file = client.files.create(
        file=open(batch_req_filename.replace('N', str(num)), "rb"), purpose="batch"
    )
    batch_input_file_id = batch_input_file.id
    print(f"running {num}")
    return client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/embeddings",
        completion_window="24h",
        metadata={"description": f"Categorized Github Recommender Embeddings Batch {num}"},
    )

def run():
    print("RUNNING Batch Files")
    b1 = run_batch_file(1)
    b2 = run_batch_file(2)
    print(f"ids: {b1.id}, {b2.id}")

def check_batch(num, id):
    status = client.batches.retrieve(id).status
    if status != "completed":
        print(f"{num}: {status}")
        return

def download():
    if len(sys.argv) < 4:
        print("Please provide both batch IDs as arguments")
        print("For example: download batch_XXX batch_XXX")
        return
    ids = [sys.argv[2].replace(',', ''), sys.argv[3].replace(',', '')]
    batches = [client.batches.retrieve(id) for id in ids]

    statuses = [batch.status for batch in batches]
    completed = all(status == "completed" for status in statuses)
    if not completed:
        print("Batches are not complete!")
        for i in len(statuses):
            print(f"{i+1}: {statuses[i]}")
        return

    print("Downloading...")
    file_ids = [batch.output_file_id for batch in batches]
    for i in range(len(file_ids)):
        filename = batch_res_filename.replace('N', str(i+1))
        content = client.files.content(file_ids[i])
        with open(filename, 'wb') as f:
            f.write(content.read())
        print(f"Saved {filename}")
    print("Done!")

def usage():
    print("Usage: python step_2.py [MODE]")
    print("Modes:")
    print("  make")
    print("    Makes the batch request files")
    print("  run")
    print("    Run the batch requests")
    print("  download BATCH_1_ID BATCH_2_ID")
    print("    Download batch results when complete")

def main():
    print("Step #2 - OpenAI Batch File")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    match mode:
        case "make":
            make()
        case "run":
            run()
        case "download":
            download()
        case "-h", "--help", "help":
            usage()
        case _:
            print("ERROR: Invalid mode")
            usage()


if __name__ == "__main__":
    main()
