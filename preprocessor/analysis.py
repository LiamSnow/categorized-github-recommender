import sys
import sqlite3

db = "data/final.sqlite"

if len(sys.argv) < 2:
    print("Please provide CLUSTER_ID as an argument (a number from 0-1999)")
    sys.exit(1)

cluster_id = sys.argv[1]

conn = sqlite3.connect(db)
cursor = conn.cursor()

cursor.execute(
    "SELECT name FROM clusters WHERE id = ?",
    (cluster_id,)
)
cluster_name = cursor.fetchone()[0]

print(f"\033[1m{cluster_name}\033[0m")

cursor.execute(
    "SELECT name_with_owner FROM repositories WHERE cluster == ?",
    (cluster_id,)
)
repo_names = cursor.fetchall()
conn.close()

for repo_name in repo_names:
    repo_name = repo_name[0]
    url = f"https://github.com/{repo_name}"
    formatted_link = f"\033]8;;{url}\033\\{repo_name}\033]8;;\033\\"
    print(f" • {formatted_link}")

