import json
from datetime import datetime
import math
from typing import List, Dict

def read_json(file: str) -> List[Dict]:
    with open(file, "r") as file:
        return json.load(file)

def save_json(path: str, data: List[Dict]) -> None:
    with open(path, "w") as file:
        json.dump(data, file, indent=2)

"""
JSON Format
---
"name_with_owner": string,
"embedding": OpenAI Embeddings (IE float array),
"stars_log": float,
"days_since_created": uint,
"days_since_pushed": uint,
"""

def main():
    print("Running Preprocessor Step #4")
    print("(1/3) reading step 3's output JSON...")
    input_data = read_json("step_3_out.json")
    print("(2/3) processing...")
    output_data = [process_repo(repo) for repo in input_data]
    print("(3/3) saving output JSON...")
    save_json("step_3_out.json", output_data)
    print("Done!")


if __name__ == "__main__":
    main()
