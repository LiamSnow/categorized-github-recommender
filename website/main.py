from flask import Flask, request, session, redirect, url_for, flash, render_template
from flask_github import GitHub
import os
import recommend
import cluster
import constants
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['GITHUB_CLIENT_ID'] = os.getenv('GITHUB_CLIENT_ID')
app.config['GITHUB_CLIENT_SECRET'] = os.getenv('GITHUB_CLIENT_SECRET')

github = GitHub(app)

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/categories")
def categories():
    return render_template('categories.html', cluster_meta=cluster.cluster_meta)

@app.route("/category/<int:id>")
def category(id):
    cluster_name = cluster.cluster_meta.get(id, [None])[0]
    if cluster_name is None:
        return "Category not found", 404
    repos = cluster.get_repos_for_cluster(id)
    return render_template('category.html', cluster_name=cluster_name, repos=repos)

@app.route("/recommendations")
def recommendations():
    if session.get('access_token', None) is None:
        return redirect(url_for('login'))
    else:
        username = session.get("username", "")
        avatar_url = session.get("avatar_url", "")

        user_repos = github.get('/user/repos') + github.get('/user/starred')
        top_clusters = cluster.get_top_clusters(user_repos)
        recs = recommend.gen_recommendations(user_repos, top_clusters)

        return render_template(
            'recommendations.html',
            username=username,
            avatar_url=avatar_url,
            recs=recs,
            cluster_meta=cluster.cluster_meta
        )

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
    next_url = request.args.get('next') or url_for('recommendations')
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
