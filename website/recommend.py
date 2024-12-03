import sqlite3
import constants
from collections import defaultdict

def gen_recommendations(user_repos, clusters):
    meta_conn = sqlite3.connect(constants.meta_db)
    meta_cursor = meta_conn.cursor()
    user_repo_names = [repo['full_name'] for repo in user_repos]

    recommendations = defaultdict(int)

    for cluster in clusters:
        recommendations[cluster] = gen_recommendations_for_cluster(user_repo_names, cluster, meta_cursor)
    return recommendations

def gen_recommendations_for_cluster(user_repo_names, cluster, meta_cursor):
    meta_cursor.execute("""
        SELECT name_with_owner, description, stars, days_since_created, days_since_pushed
        FROM repositories
        WHERE cluster = ?
    """, (cluster,))
    repo_data = meta_cursor.fetchall()

    # make sure we don't recommend a repo the user has made/starred
    user_repo_set = set(user_repo_names)
    repos = [repo for repo in repo_data if repo[0] not in user_repo_set]

    scored_repos = [(repo, score_repo(repo)) for repo in repos]
    scored_repos.sort(key=lambda x: x[1], reverse=True)

    return [pair[0] for pair in scored_repos[:constants.num_recommendations]]

# TODO
def score_repo(repo):
    _, _, stars, days_since_created, days_since_pushed = repo
    recency_score = max(0, 365 - days_since_pushed) / 365
    return stars

