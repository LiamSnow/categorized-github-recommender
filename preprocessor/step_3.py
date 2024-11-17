import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from umap import UMAP
import sqlite3
from mpl_toolkits.mplot3d import Axes3D

# Reference: https://cookbook.openai.com/examples/clustering

num_clusters = 2000
input_files = ["data/step_2_out_1.jsonl", "data/step_2_out_2.jsonl"]

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
    umap = UMAP(n_neighbors=3, min_dist=0.8, n_components=3, spread=1.5)
    vis_dims3 = umap.fit_transform(matrix)

    x = [x for x, y, z in vis_dims3]
    y = [y for x, y, z in vis_dims3]
    z = [z for x, y, z in vis_dims3]

    unique_clusters = np.unique(clusters)
    colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_clusters)))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for i, cluster in enumerate(unique_clusters):
        mask = clusters == cluster
        xs = np.array(x)[mask]
        ys = np.array(y)[mask]
        zs = np.array(z)[mask]
        color = colors[i]
        ax.scatter(xs, ys, zs, color=color, alpha=0.3, s=1)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title("Cluster Visualization")
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
    print("Step #3 - Clustering")

    print("parsing files...")
    names1, matrix1 = read_jsonl(input_files[0])
    names2, matrix2 = read_jsonl(input_files[1])
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
