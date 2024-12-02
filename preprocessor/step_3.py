import json
import numpy as np
from sklearn.cluster import KMeans
import sqlite3
import chromadb

# Reference: https://cookbook.openai.com/examples/clustering

num_clusters = 2000
input_files = ["data/step_2_out_1.jsonl", "data/step_2_out_2.jsonl"]
source_db = "data/step_1_out.sqlite"
dest_db = "data/step_3_out.sqlite"
embeddings_db = "data/embeddings/"

def read_jsonl(filename):
    names = []
    embeddings = []
    with open(filename, "r") as file:
        for line in file:
            obj = json.loads(line)
            names.append(obj["custom_id"])
            embeddings.append(obj["response"]["body"]["data"][0]["embedding"])
    names = np.array(names)
    matrix = np.vstack(embeddings)
    return names, matrix


def kmeans(matrix, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", random_state=42)
    kmeans.fit(matrix)
    labels = kmeans.labels_
    return labels

def copy_insert_db(source_db, dest_db, name_with_owners, clusters):
    with open(source_db, "rb") as src, open(dest_db, "wb") as dst:
        dst.write(src.read())
    conn = sqlite3.connect(dest_db)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE repositories ADD COLUMN cluster INTEGER DEFAULT -1")
    conn.commit()
    for name_with_owner, cluster in zip(name_with_owners, clusters):
        cursor.execute(
            """
            UPDATE repositories
            SET cluster = ?
            WHERE name_with_owner = ?
        """,
            (int(cluster), name_with_owner),
        )
    conn.commit()
    conn.close()

def make_chroma(names, matrix, embeddings_db):
    client = chromadb.PersistentClient(path=embeddings_db)
    collection = client.create_collection("embeddings")
    batch_size = 10000
    total_embeddings = len(names)
    for i in range(0, total_embeddings, batch_size):
        end_idx = min(i + batch_size, total_embeddings)
        batch_embeddings = matrix[i:end_idx].tolist()
        batch_names = names[i:end_idx].tolist()
        collection.add(
            embeddings=batch_embeddings,
            ids=batch_names,
        )
        print(f" -> {i//batch_size + 1}/{(total_embeddings + batch_size - 1)//batch_size}")

def main():
    print("Step #3 - Clustering & Make Vector DB")

    print("parsing files")
    names1, matrix1 = read_jsonl(input_files[0])
    names2, matrix2 = read_jsonl(input_files[1])
    names = np.concatenate((names1, names2))
    matrix = np.vstack((matrix1, matrix2))

    print(f"making embeddings db ({embeddings_db})")
    make_chroma(names, matrix, embeddings_db)

    print("running kmeans")
    clusters = kmeans(matrix, num_clusters)

    print(f"copying {source_db} to {dest_db} with cluster column added")
    copy_insert_db(source_db, dest_db, names, clusters)

    print("Done!")


if __name__ == "__main__":
    main()
