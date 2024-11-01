from dotenv import load_dotenv
import os
from github import Github
from github import Auth
import csv

load_dotenv()

auth = Auth.Token(os.environ['GITHUB_API_KEY'])

g = Github(auth=auth)

min_stars = 50
header = ['id', 'name', 'stars', 'desc']
num_repos = 128e6

with open('data.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=header)
    writer.writeheader()
    for repo in g.get_repos():
        # if repo.id % 100 == 0:
        print(f"{repo.id}/{num_repos} ({repo.id/num_repos:.4f}%)\n")
        if repo.stargazers_count < min_stars:
           continue
        writer.writerow({
            'id': repo.id,
            'name': repo.name,
            'stars': repo.stargazers_count,
            'desc': repo.description
        })



# user = g.get_user()
#
# for starred in user.get_starred():
#     print(starred.name + " " + str(starred.stargazers_count))

g.close()
