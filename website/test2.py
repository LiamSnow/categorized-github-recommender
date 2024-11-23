import requests
from flask import Flask, redirect, request, session, url_for, render_template # type: ignore
from github import Github
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace these with your GitHub client ID and secret
client_id = ""  # your id
client_secret = ""  # your secret
<<<<<<< HEAD
redirect_uri = ""
=======
redirect_uri = "http://127.0.0.1:5000/callback"
>>>>>>> 0f3c269ea428a84f25e5152c6c4b1ee73c6fb66e

auth_url = "https://github.com/login/oauth/authorize"
token_url = "https://github.com/login/oauth/access_token"

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login')
def login():
    url_1 = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo,user"
    return redirect(url_1)


@app.route('/callback')
def callback():
    code = request.args.get("code")
    if not code:
        return "Error: Missing authorization code"

    # Exchange the code for an access token
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

    # Use PyGithub to get the authenticated user's info
    g = Github(access_token)
    user = g.get_user()

    return render_template("welcome.html", username=user.login)


@app.route('/repos')
def repos():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    # Use PyGithub to fetch repositories
    g = Github(access_token)
    user = g.get_user()
    repos_data = []

    # Collect relevant repository details
    for repo in user.get_repos():
        print(f"Name: {repo.name}, Stars: {repo.stargazers_count}, Description: {repo.description}")  # Debugging
        repos_data.append({
            "name": repo.name,
            "description": repo.description or "No description provided",
            "stars": repo.stargazers_count,
            "languages": repo.language
        })

    return render_template("repos.html", repos=repos_data)





@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response


if __name__ == "__main__":
    app.run(debug=True)
