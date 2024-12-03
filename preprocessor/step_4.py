from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import random
import sys
import json

# Reference: https://platform.openai.com/docs/guides/batch
# View Batches: https://platform.openai.com/batches

min_words = 4
max_words = 10
num_samples = 20 # how many samples from each cluster is included in prompt
source_db = "data/step_3_out.sqlite"
dest_db = "output/final.sqlite"
batch_req_file = "data/step_4_batch.jsonl"
batch_res_file = "data/step_4_out.jsonl"

load_dotenv()
client = OpenAI()

def prompt(repos_str):
    return f"Analyze the following GitHub repositories and create a concise, " \
            f"descriptive category name ({min_words}-{max_words} words) that " \
            f"encompasses their common theme, technology stack, or purpose:\n\n" \
            f"Repositories:\n{repos_str}\n\nCategory Name:"

def make_openai_req(cluster_id, repos_str):
    return json.dumps(
        {
            "custom_id": str(cluster_id),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt(repos_str)
                    }
                ],
                "temperature": 0.4,
                "max_tokens": 30,
                "top_p": 0.9,
                "frequency_penalty": 0.2,
                "presence_penalty": 0.2,
            },
        }
    )

def make():
    print("MAKING Batch File")

    print(f"reading {source_db}")
    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name_with_owner, name, description, topics, languages, cluster FROM repositories"
    )
    repos = cursor.fetchall()
    conn.close()

    unique_clusters = list(set(repo[5] for repo in repos))  # cluster is at index 5
    print(f"processing {len(unique_clusters)} clusters!")

    with open(batch_req_file, "w") as batch_file:
        for cluster_id in unique_clusters:
            cluster_repos = [repo for repo in repos if repo[5] == cluster_id]
            sample_repos = random.sample(cluster_repos, min(num_samples, len(cluster_repos)))
            repos_str = ""
            for repo in sample_repos:
                name_with_owner, _, description, topics, languages, _ = repo
                repos_str += f"{name_with_owner}: {description} | Topics: {topics} | Languages: {languages}\n"
            batch_file.write(make_openai_req(cluster_id, repos_str) + "\n")

def run():
    print("RUNNING Batch File")
    print("uploading file")
    batch_input_file = client.files.create(
        file=open(batch_req_file, "rb"), purpose="batch"
    )
    batch_input_file_id = batch_input_file.id
    print("running")
    batch_id = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": f"CS 547 Final Project Categorizing Batch"},
    )
    print(f"batch_id = {batch_id}")

def download():
    if len(sys.argv) < 3:
        print("Please provide batch ID as argument!")
        print("For example: download batch_xxx")
        return

    batch_id = sys.argv[2]
    batch = client.batches.retrieve(batch_id)

    if batch.status != "completed":
        print(f"Batch is not complete! Currently: {batch.status}")
        return

    print(f"Downloading {batch_res_file}...")
    content = client.files.content(batch.output_file_id)
    with open(batch_res_file, 'wb') as f:
        f.write(content.read())
    print("Done!")

def finalize():
    print("FINALIZING")
    print("copying db")
    with open(source_db, "rb") as src, open(dest_db, "wb") as dst:
        dst.write(src.read())
    conn = sqlite3.connect(dest_db)
    cursor = conn.cursor()

    print("making clusters table")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    ''')
    conn.commit()

    print(f"finalizing {batch_res_file} into db")
    with open(batch_res_file, "r") as file:
        for line in file:
            obj = json.loads(line)
            cluster_id = obj["custom_id"]
            cluster_name = obj["response"]["body"]["choices"][0]["message"]["content"]
            cluster_name = cluster_name.strip('*').strip('"') # remove markdown bold and quotes
            cursor.execute('''
            INSERT INTO clusters (id, name)
            VALUES (?, ?)
            ''', (cluster_id, cluster_name))
            conn.commit()
    conn.close()
    print("Done!")

def usage():
    print("Usage: python step_4.py [MODE]")
    print("Modes:")
    print("  make")
    print("    Makes the batch request file")
    print("  run")
    print("    Run the batch request")
    print("  download BATCH_ID")
    print("    Download batch results when complete")
    print("  finalize")
    print("    Convert the batch results to the final.sqlite db")

def main():
    print("Step #4 - Cluster Labeling (Categorization)")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    match mode:
        case "make":
            make()
        case "run":
            run()
        case "download":
            download()
        case "finalize":
            finalize()
        case "-h", "--help", "help":
            usage()
        case _:
            print("ERROR: Invalid mode")
            usage()

if __name__ == "__main__":
    main()
