import sqlite3
from openai import OpenAI
from collections import Counter
import chromadb
from collections import defaultdict
import constants
from dotenv import load_dotenv
import recommend

load_dotenv()

client = OpenAI()

# this is not too big we can bring it all into memory
def get_all_cluster_meta():
    conn = sqlite3.connect(constants.meta_db)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, stars FROM clusters ORDER BY stars DESC")
    clusters = cursor.fetchall()
    conn.close()
    return {row[0]: (row[1], row[2]) for row in clusters}
cluster_meta = get_all_cluster_meta()

# cache stores kNN result so we don't have to embed all the time
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

# returns [clusters:occurances] in given list of repos
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

# returns list of cluster_id's of top N clusters that occur in the repos list
def get_top_clusters(repos):
    cluster_map = get_clusters(repos)
    top_clusters_map = Counter(cluster_map).most_common(constants.num_categories)
    return [id for id, _ in top_clusters_map]

# gets known cluster for repo (in either meta or cache)
def get_repo_cluster(name_with_owner, cursor):
    cursor.execute(
        "SELECT cluster FROM repositories WHERE name_with_owner = ?",
        (name_with_owner,)
    )
    result = cursor.fetchone()
    if result:
        return result[0]

# Uses kNN to classify unknown repo into existing dataset
# by using cosine similarity between OpenAI embeddings
def gen_repo_cluster(repo, chroma_collection, meta_cursor, cache_conn, cache_cursor):
    # embed this repo
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

    response = client.embeddings.create(
        input=embedding_text,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    # find N most similar repos
    similar_repos = chroma_collection.query(
        query_embeddings=[embedding],
        n_results=10,
        include=["documents"]
    )

    # choose common cluster between N most similar repos
    similar_repo_ids = similar_repos['ids'][0]
    placeholders = ','.join(['?' for _ in similar_repo_ids])
    meta_cursor.execute(f"""
        SELECT name_with_owner, cluster
        FROM repositories
        WHERE name_with_owner IN ({placeholders})
    """, similar_repo_ids)
    clusters = dict(meta_cursor.fetchall())
    cluster_counts = Counter(clusters.values())
    cluster = cluster_counts.most_common(1)[0][0] if cluster_counts else None

    # save to cache
    cache_cursor.execute('''
        INSERT into repositories (name_with_owner, cluster)
        VALUES (?, ?)
    ''', (repo['full_name'], cluster))
    cache_conn.commit()

    return cluster

def get_repos_for_cluster(cluster_id):
    conn = sqlite3.connect(constants.meta_db)
    cursor = conn.cursor()
    repos = recommend.gen_recommendations_for_cluster(None, cluster_id, cursor, False)
    conn.close()
    return repos


