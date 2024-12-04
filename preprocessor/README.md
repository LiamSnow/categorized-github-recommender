# Preprocessor

This subrepo will take a giant JSON file from Kaggle with metadata from
every GitHub repository that has over 5 stars, filter them, embed them
(using OpenAI embeddings), cluster them (using K-Means), and finally
label the clusters. In effect, this categorizes every GitHub repository,
entirely unsupervised.

You can view the results of the clustering by running `python analysis.py CLUSTER_ID(0-1999)`!

## Files
Since this is a large task at hand, the process is split into four files:

`step_1.py`: Filters repos and saves their relevant metadata into a SQLite database (for faster access)

`step_2.py`: Creates and executes a multiple batch requests to OpenAI servers to embed each repositories metadata (name, description, langauges, topics)

`step_3.py`: Uses K-Means to cluster each the repositories using their embeddings

`step_4.py`: Uses ChatGPT to create a name for each cluster

## Output
The final output of the preprocessor is:
 - `output/meta.sqlite`: A SQLite database containing two tables `repositories` and `clusters` shown below
 - `output/embeddings/`: A ChromaDB that maps `name_with_owner` -> embeddings for similarity search

```sql
TABLE clusters (
    id INTEGER PRIMARY KEY,
    name TEXT
)

TABLE repositories (
    name_with_owner TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    topics TEXT,
    languages TEXT,
    stars INTEGER,
    days_since_created INTEGER,
    days_since_pushed INTEGER,
    FOREIGN KEY (cluster) REFERENCES clusters(id)
)
```

## Dataset
The dataset is from [Kaggle](https://www.kaggle.com/datasets/pelmers/github-repository-metadata-with-5-stars)

## Running
1. Download the dataset it, extract it, and save it to `data/repo_metadata.json`.
2. Run `step_1.py` (you can adjust the `meets_requirements` method to change how many repos get filtered)
3. Add `OPENAI_API_KEY` to a `.env` file
4. Run `step_2.py make` then `step_2.py run`
5. After a few hours, run `step_2.py download` which will download the files once both batch processes are complete
6. Run `step_3.py` (you can adjust `num_clusters`)
7. Run `step_4.py make` then `step_4.py run`
8. After ~hour, run `step_4.py download`, then `step_4.py finalize`
9. All done! You now have your `final.sqlite`

