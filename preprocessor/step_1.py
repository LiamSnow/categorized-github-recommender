import json
from typing import List, Dict

def read_json(file: str) -> List[Dict]:
    with open(file, 'r') as file:
        return json.load(file)

def meets_requirements(repo: Dict) -> bool:
    # TODO FIXME change to full dataset
    return repo['stars'] > 10000 and not repo['isArchived']

def filter_qualifying_repos(repos: List[Dict]) -> List[Dict]:
    return [repo for repo in repos if meets_requirements(repo)]

def save_json(path: str, data: List[Dict]) -> None:
    with open(path, 'w') as file:
        json.dump(data, file, indent=2)

if __name__ == "__main__":
    print("Running Preprocessor Step #1")
    print("(1/4) reading dataset (this will take awhile)...")
    repos = read_json('repo_metadata.json')

    print("(2/4) filtering...")
    qualifying_repos = filter_qualifying_repos(repos)

    print(f"filter down to {len(qualifying_repos)} repos")

    print("(3/4) saving file...")
    save_json('step_1_out.json', qualifying_repos)

    print("Done!")
    print("(4/4) please wait for deallocation...")
