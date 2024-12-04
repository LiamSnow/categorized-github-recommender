# Website

## Running
 1. Install python packages from `requirements.txt`
 2. Get an OpenAI api key
 3. Make a GitHub App
 4. Generate a secret key for flask:
```bash
openssl rand -hex 32
```
 5. Create `.env` and set the following:
```env
OPENAI_API_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
FLASK_SECRET_KEY=
```
