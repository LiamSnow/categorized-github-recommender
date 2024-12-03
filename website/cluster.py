import sqlite3
from datetime import datetime
from openai import OpenAI
from collections import Counter
import chromadb
from collections import defaultdict
import constants

client = OpenAI()

def get_all_cluster_names():
    conn = sqlite3.connect(constants.meta_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM clusters")
    clusters = dict(cursor.fetchall())
    conn.close()
    return clusters
cluster_names = get_all_cluster_names()

def make_cache_table():
    cache_conn = sqlite3.connect(constants.cache_db)
    cache_cursor = cache_conn.cursor()
    cache_cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        name_with_owner TEXT PRIMARY KEY,
        cluster INTEGER
    )
    ''')
    cache_conn.close()
make_cache_table()

def get_clusters(repos):
    meta_conn = sqlite3.connect(constants.meta_db)
    meta_cursor = meta_conn.cursor()
    cache_conn = sqlite3.connect(constants.cache_db)
    cache_cursor = cache_conn.cursor()
    chroma_client = chromadb.PersistentClient(path=constants.embeddings_db)
    chroma_collection = chroma_client.get_collection("embeddings")

    clusters = defaultdict(int)

    for repo in repos:
        name_with_owner = repo['full_name']
        cluster = get_repo_cluster(name_with_owner, meta_cursor)
        if not cluster:
            cluster = get_repo_cluster(name_with_owner, cache_cursor)
        if not cluster:
            cluster = gen_repo_cluster(repo, chroma_collection, meta_cursor, cache_conn, cache_cursor)
        clusters[cluster] += 1

    meta_conn.close()
    cache_conn.close()

    return clusters

def get_repo_cluster(name_with_owner, cursor):
    cursor.execute(
        "SELECT cluster FROM repositories WHERE name_with_owner = ?",
        (name_with_owner,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]

# this is essentially kNN
def gen_repo_cluster(repo, chroma_collection, meta_cursor, cache_conn, cache_cursor):
    print(f"GEN {repo['full_name']}")
    try:
        topics = ', '.join(repo.get("topics", []))
    except TypeError:
        print(f"Warning: Unexpected format for topics in repo {repo['full_name']}")
        topics = ''
    try:
        languages = ', '.join(repo.get("languages", [])[:3])
    except TypeError:
        print(f"Warning: Unexpected format for languages in repo {repo['full_name']}")
        languages = ''
    embedding_text = f"{repo['name']} {repo['description']} {topics} {languages}"
    print(f"embedding_text={embedding_text}")

    response = client.embeddings.create(
        input=embedding_text,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    similar_repos = chroma_collection.query(
        query_embeddings=[embedding],
        n_results=10,
        include=["documents"]
    )

    similar_repo_ids = similar_repos['ids'][0]
    print(f"similar_repo_ids={similar_repo_ids}")
    placeholders = ','.join(['?' for _ in similar_repo_ids])
    meta_cursor.execute(f"""
        SELECT name_with_owner, cluster
        FROM repositories
        WHERE name_with_owner IN ({placeholders})
    """, similar_repo_ids)
    clusters = dict(meta_cursor.fetchall())
    print(f"clusters={clusters}")

    cluster_counts = Counter(clusters.values())
    cluster = cluster_counts.most_common(1)[0][0] if cluster_counts else None
    print(f"cluster={cluster}")

    cache_cursor.execute('''
        INSERT into repositories (name_with_owner, cluster)
        VALUES (?, ?)
    ''', (repo['full_name'], cluster))
    cache_conn.commit()

    return cluster
