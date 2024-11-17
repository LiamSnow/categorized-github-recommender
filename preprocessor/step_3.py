import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from umap import UMAP
import sqlite3

# Reference: https://cookbook.openai.com/examples/clustering

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

def visualize(matrix, clusters):
    umap = UMAP(n_neighbors=5, min_dist=0.5, n_components=2)
    vis_dims2 = umap.fit_transform(matrix)

    x = [x for x, y in vis_dims2]
    y = [y for x, y in vis_dims2]
    unique_clusters = np.unique(clusters)
    colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_clusters)))

    for i, cluster in enumerate(unique_clusters):
        mask = clusters == cluster
        xs = np.array(x)[mask]
        ys = np.array(y)[mask]
        color = colors[i]
        plt.scatter(xs, ys, color=color, alpha=0.3, label=f"Cluster {cluster}", s=1)

    plt.title("Cluster Visualiziation")
    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.savefig("data/cluster_visualization.png", dpi=300, bbox_inches="tight")
    plt.close()


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

def main():
    num_clusters = 100
    print("Step #3 - Clustering")

    print("parsing files...")
    names1, matrix1 = read_jsonl("data/step_2_out_1.jsonl")
    names2, matrix2 = read_jsonl("data/step_2_out_2.jsonl")
    names = np.concatenate((names1, names2))
    matrix = np.vstack((matrix1, matrix2))

    print("running kmeans")
    clusters = kmeans(matrix, num_clusters)

    print("saving to new db")
    copy_insert_db("data/step_1_out.sqlite", "data/step_3_out.sqlite", names, clusters)

    print("visualizing")
    visualize(matrix, clusters)

    print("Done!")


if __name__ == "__main__":
    main()
