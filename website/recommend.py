import sqlite3
import constants
from collections import defaultdict
import math

# generates N recommendations for each cluster
def gen_recommendations(user_repos, clusters):
    meta_conn = sqlite3.connect(constants.meta_db)
    meta_cursor = meta_conn.cursor()
    user_repo_names = [repo['full_name'] for repo in user_repos]

    recommendations = defaultdict(int)

    for cluster in clusters:
        recommendations[cluster] = gen_recommendations_for_cluster(user_repo_names, cluster, meta_cursor)
    return recommendations

def gen_recommendations_for_cluster(user_repo_names, cluster, meta_cursor, limit=True):
    # get all repos for cluster
    meta_cursor.execute("""
        SELECT name_with_owner, description, stars, days_since_created, days_since_pushed
        FROM repositories
        WHERE cluster = ?
    """, (cluster,))
    repos = meta_cursor.fetchall()

    # exclude repos that the user has created/starred
    if user_repo_names is not None:
        user_repo_set = set(user_repo_names)
        repos = [repo for repo in repos if repo[0] not in user_repo_set]

    # rank repos (and remove those with score=0)
    scored_repos = [(repo, score) for repo in repos if (score := score_repo(repo)) > 0]
    scored_repos.sort(key=lambda x: x[1], reverse=True)

    # return top N repos
    if limit:
        return [pair[0] for pair in scored_repos[:constants.num_recommendations]]
    else:
        return [pair[0] for pair in scored_repos]

# GOAL: recommend up and coming / interesting repositories
def score_repo(repo):
    _, _, stars, days_since_created, days_since_pushed = repo

    # fixing messed up preprocessor data
    days_since_created -= 456
    days_since_pushed -= 456

    # only want active projects
    if days_since_pushed > 365:
        return 0

    # younger projects are better, but only slightly
    age_score = 0.7
    if days_since_created < 180:
        age_score = 1.0
    elif days_since_created < 730:
        age_score = 0.9
    elif days_since_created < 1460:
        age_score = 0.8

    star_score = math.log10(stars + 1)

    return age_score * star_score

