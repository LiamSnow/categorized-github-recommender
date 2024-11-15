import json
from datetime import datetime
import math
from typing import List, Dict
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from sklearn.cluster import DBSCAN

NUM_DIMENSIONS = 1536 + 3
MIN_POINTS = 3 # NUM_DIMENSIONS * 2
EPSILON = 1.0 # this will be tweaked

def read_db(name):
    conn = sqlite3.connect(name)
    cursor = conn.cursor()
    cursor.execute("SELECT name_with_owner, embedding FROM repositories")
    rows = cursor.fetchall()
    conn.close()
    return rows

def conv_data(rows):
    data = []
    repo_names = []
    for row in rows:
        (name_with_owner, embedding_blob) = row
        data.append(json.loads(embedding_blob))
        repo_names.append(name_with_owner)
    return np.array(data)

def run_dbscan(X, epsilon, min_points):
    print(f"running DBSCAN with min_points={min_points} epsilon={epsilon}")
    dbscan = DBSCAN(eps=epsilon, min_samples=min_points)
    clusters = dbscan.fit_predict(X)
    num_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
    num_noise = list(clusters).count(-1)
    print(f' -> Results: {num_clusters} clusters, {num_noise} noise points')
    return num_clusters, num_noise

def main():
    print("Running Preprocessor Step #3")

    print("(1/4) opening step 2's output db...")
    rows = read_db("step_2_out.sqlite")

    print("(2/4) converting data...")
    X = conv_data(rows)

    # e_values = []
    # noise_points = []
    #
    # for e in range(1, 50):
    #     num_clusters, num_noise = run_dbscan(X, e, 5)
    #     e_values.append(e)
    #     noise_points.append(num_noise)
    #
    # plt.figure(figsize=(10, 6))
    # plt.plot(e_values, noise_points, marker='o')
    # plt.xlabel('Epsilon (e)')
    # plt.ylabel('Number of Noise Points')
    # plt.title('Epsilon vs Number of Noise Points in DBSCAN')
    # plt.grid(True)
    # plt.show()

    m_values = []
    noise_points = []

    for m in range(2, 10):
        num_clusters, num_noise = run_dbscan(X, 20, m)
        m_values.append(m)
        noise_points.append(num_noise)

    plt.figure(figsize=(10, 6))
    plt.plot(m_values, noise_points, marker='o')
    plt.xlabel('Min Points (m)')
    plt.ylabel('Number of Noise Points')
    plt.title('Min Points vs Number of Noise Points in DBSCAN (e=5)')
    plt.grid(True)
    plt.show()

    # print("(4/4) saving output db...")
    # output_conn = sqlite3.connect("step_3_out.sqlite")
    # output_cursor = output_conn.cursor()
    # output_cursor.execute("""
    # CREATE TABLE IF NOT EXISTS clustered_repositories (
    #     name_with_owner TEXT PRIMARY KEY,
    #     cluster_id INTEGER
    # )
    # """)
    # for name, cluster_id in zip(repo_names, clusters):
    #     output_cursor.execute("INSERT OR REPLACE INTO clustered_repositories (name_with_owner, cluster_id) VALUES (?, ?)",
    #                           (name, int(cluster_id)))
    # output_conn.commit()
    # output_conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
