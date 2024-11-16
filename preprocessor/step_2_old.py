from dotenv import load_dotenv
import sqlite3
from openai import OpenAI
from sklearn.decomposition import PCA
import numpy as np

load_dotenv()
client = OpenAI()

def read_db(name):
    input_conn = sqlite3.connect(name)
    input_cursor = input_conn.cursor()
    input_cursor.execute("SELECT name_with_owner, name, description, topics, languages FROM repositories")
    rows = input_cursor.fetchall()
    input_conn.close()
    return rows

def create_db(name):
    conn = sqlite3.connect(name)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        name_with_owner TEXT PRIMARY KEY,
        embedding BLOB
    )
    ''')
    conn.commit()
    return conn, cursor

def save_repo(name_with_owner, embedding, cursor):
    try:
        cursor.execute('''
        INSERT INTO repositories (name_with_owner, embedding)
        VALUES (?, ?)
        ''', (
            name_with_owner,
            embedding.tobytes(),
        ))
    except sqlite3.IntegrityError:
        print(f"WARNING: Duplicate entry {name_with_owner}")
    except Exception as e:
        print(f"WARNING: Error inserting {name_with_owner}: {str(e)}")

def embed(text: str):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def embed_repo(repo):
    (name_with_owner, name, description, topics, languages) = repo
    embedding_text = f"{name} {description} {topics} {languages}"
    embedding = embed(embedding_text)
    return name_with_owner, embedding

def embed_repos(repos):
    names = []
    embeddings = []
    for repo in repos:
        name_with_owner, embedding = embed_repo(repo)
        names.append(name_with_owner)
        embeddings.append(embedding)
    return np.array(names), np.array(embeddings)

def main():
    print("Running Preprocessor Step #2")
    print("(1/X) reading step 1 output db...")
    input_repos = read_db("step_1_out.sqlite")

    print("(2/X) embedding...")
    (names, embeddings) = embed_repos(input_repos)

    print("(3/X) reducing dimensions...")
    pca = PCA(n_components=100)
    reduced_embeddings = pca.fit_transform(embeddings)

    print("(4/X) creating database...")
    conn, cursor = create_db("step_2_out.sqlite")
    for i in range(len(names)):
        save_repo(names[i], reduced_embeddings[i], cursor)

    print("(5/X) saving...")
    conn.commit()
    conn.close()

    print("Done!")

if __name__ == "__main__":
    main()
