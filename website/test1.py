from flask import Flask, redirect, request, session, url_for, render_template  # type: ignore
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace theswe with your GitHub client ID and secret
client_id = " "  # your id
client_secret = " "  # your secret
redirect_uri = ""

auth_url = "https://github.com/login/oauth/authorize"
tok_url = "https://github.com/login/oauth/access_token"
userid = "https://api.github.com/user"

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
        tok_url,
        headers={"Accept": "application/json"},
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
    )
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Error: Could not retrieve access token"

    session['access_token'] = access_token
    headers = {"Authorization": f"token {access_token}"}
    user_response = requests.get(userid, headers=headers)
    user_data = user_response.json()

    return render_template("welcome.html", username=user_data['login'])


@app.route('/repos')
def repos():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"token {access_token}"}
    repos_response = requests.get("https://api.github.com/user/repos", headers=headers)
    repos_data = repos_response.json()

    return render_template("repos.html", repos=repos_data)

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response



if __name__ == "__main__":
    app.run(debug=True)
