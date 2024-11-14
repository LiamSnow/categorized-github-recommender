import json
from datetime import datetime
import math
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from sklearn.cluster import DBSCAN

NUM_DIMENSIONS = 1536 + 3
MIN_POINTS = 5 # NUM_DIMENSIONS * 2
EPSILON = 15.0 # this will be tweaked

"""
CREATE TABLE IF NOT EXISTS repositories (
    name_with_owner TEXT PRIMARY KEY,
    embedding BLOB, # json blob, float[1536]
    stars_log REAL,
    days_since_created INTEGER,
    days_since_pushed INTEGER
)
"""

def main():
    print("Running Preprocessor Step #4")

    print("(1/4) opening step 3's output db...")
    input_conn = sqlite3.connect("step_3_out.sqlite")
    input_cursor = input_conn.cursor()
    input_cursor.execute("SELECT name_with_owner, embedding, stars_log, days_since_created, days_since_pushed FROM repositories")
    rows = input_cursor.fetchall()
    input_conn.close()

    print("(2/4) converting data...")
    data = []
    repo_names = []
    for row in rows:
        name_with_owner, embedding_blob, stars_log, days_since_created, days_since_pushed = row
        embedding = json.loads(embedding_blob)
        features = embedding + [stars_log, days_since_created, days_since_pushed]
        data.append(features)
        repo_names.append(name_with_owner)
    X = np.array(data)

    print("(3/4) running DBSCAN...")
    dbscan = DBSCAN(eps=EPSILON, min_samples=MIN_POINTS)
    clusters = dbscan.fit_predict(X)
    num_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
    num_noise = list(clusters).count(-1)
    print(f' -> Results: {num_clusters} clusters, {num_noise} noise points')

    print("(4/4) saving output db...")
    output_conn = sqlite3.connect("step_4_out.sqlite")
    output_cursor = output_conn.cursor()
    output_cursor.execute("""
    CREATE TABLE IF NOT EXISTS clustered_repositories (
        name_with_owner TEXT PRIMARY KEY,
        cluster_id INTEGER
    )
    """)
    for name, cluster_id in zip(repo_names, clusters):
        output_cursor.execute("INSERT OR REPLACE INTO clustered_repositories (name_with_owner, cluster_id) VALUES (?, ?)",
                              (name, int(cluster_id)))
    output_conn.commit()
    output_conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
