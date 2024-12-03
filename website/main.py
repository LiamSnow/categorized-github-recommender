from flask import Flask, request, session, redirect, url_for, flash
from flask_github import GitHub
from dotenv import load_dotenv
import os
import recommend
import cluster
import constants

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['GITHUB_CLIENT_ID'] = os.getenv('GITHUB_CLIENT_ID')
app.config['GITHUB_CLIENT_SECRET'] = os.getenv('GITHUB_CLIENT_SECRET')

github = GitHub(app)

@app.route("/")
def index():
    if session.get('access_token', None) is None:
        return '<a href="/login">Login</a>'
    else:
        username = session.get("username", "")
        avatar_url = session.get("avatar_url", "")

        user_repos = github.get('/user/repos') + github.get('/user/starred')
        top_clusters = cluster.get_top_clusters(user_repos)

        rhtml = "<h2>Recommendations</h2>"
        recs = recommend.gen_recommendations(user_repos, top_clusters)
        for cluster_id, repos in recs.items():
            rhtml += '<div style="border: 1px solid black; margin: 10px; padding: 10px;">'
            rhtml += f'<h4 style="text-decoration: underline;">{cluster.cluster_names[cluster_id]}</h4>'
            for repo in repos:
                name, desc, stars, _, _ = repo
                link = f'<a href="https://github.com/{name}">{name}</a>'
                rhtml += f"<p>{link} [{stars}]: {desc}</p>"
            rhtml += "</div>"

        return f'<img src="{avatar_url}" style="width:50px" />' + f'<span>{username}</span>' + '<a href="/logout">Logout</a>' + rhtml

@app.route('/login')
def login():
    if session.get('access_token', None) is None:
        return github.authorize(redirect_uri=f"{constants.domain}/github-callback")
    else:
        return 'Already logged in'

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('avatar_url', None)
    return redirect(url_for('index'))

@github.access_token_getter
def token_getter():
    return session.get('access_token', None)

@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        flash("Authorization failed.")
        return redirect(next_url)
    session['access_token'] = access_token
    print("LOGGED IN")
    github_user = github.get('/user')
    session['id'] = github_user['id']
    session['username'] = github_user['login']
    session['avatar_url'] = github_user['avatar_url']
    return redirect(next_url)
