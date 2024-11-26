import requests
from flask import Flask, redirect, request, session, url_for, render_template, send_file
from github import Github
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import sqlite3
import pandas as pd
import os
import csv
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")

auth_url = "https://github.com/login/oauth/authorize"
token_url = "https://github.com/login/oauth/access_token"


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/login')
def login():
    url_1 = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo,user"
    return redirect(url_1)


@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: Missing authorization code"

    token_response = requests.post(
        token_url,
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Error: Could not retrieve access token"

    session['access_token'] = access_token

    g = Github(access_token)
    user = g.get_user()

    return render_template("welcome.html", username=user.login)


@app.route('/repos')
def repos():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    g = Github(access_token)
    user = g.get_user()
    repos_data = []
    csv_file = "repositories.csv"

    for repo in user.get_repos():
        repos_data.append({
            "name": repo.name,
            "description": repo.description or "No description provided",
            "stars": repo.stargazers_count,
            "languages": repo.language
        })

    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "description", "stars", "languages"])
        writer.writeheader()
        writer.writerows(repos_data)

    return render_template("repos.html", repos=repos_data)


@app.route('/recommendations')
def recommendations():
    sqlite_file = "final.sqlite"  #add filepath
    conn = sqlite3.connect(sqlite_file)
    repositories = pd.read_sql_query("SELECT * FROM repositories", conn)

    if repositories.empty:
        conn.close()
        return "No repositories found in the database."

    user_preferences = pd.read_csv("repositories.csv")
    repo_features = repositories[['languages', 'stars']]
    repo_features = pd.get_dummies(repo_features, columns=['languages'], dummy_na=True)

    user_features = user_preferences[['languages']]
    user_features = pd.get_dummies(user_features, columns=['languages'], dummy_na=True)
    user_features = user_features.reindex(columns=repo_features.columns, fill_value=0)

    scaler = StandardScaler()
    scaled_repo_features = scaler.fit_transform(repo_features)
    scaled_user_features = scaler.fit_transform(user_features)

    knn = NearestNeighbors(n_neighbors=5, metric='cosine')
    knn.fit(scaled_repo_features)

    recommendations = []
    for user_index, user_vector in enumerate(scaled_user_features):
        user_vector = user_vector.reshape(1, -1)
        distances, indices = knn.kneighbors(user_vector)
        recommended_repos = [repositories.iloc[i]['name'] for i in indices[0]]
        recommendations.append({"user": f"User {user_index}", "recommendations": recommended_repos})

    conn.close()
    return render_template("recommendations.html", recommendations=recommendations)


@app.route('/favicon.ico')
def favicon():
    return '', 204


if __name__ == "__main__":
    app.run(debug=True)
