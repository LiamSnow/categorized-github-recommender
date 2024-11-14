# Preprocessing

## Dataset
The dataset is from [Kaggle](https://www.kaggle.com/datasets/pelmers/github-repository-metadata-with-5-stars).

## Data Format
Data is a array of repo metadata, for example:
```json
{
  "owner": "pelmers",
  "name": "text-rewriter",
  "stars": 13,
  "forks": 5,
  "watchers": 4,
  "isFork": false,
  "isArchived": false,
  "languages": [ { "name": "JavaScript", "size": 21769 }, { "name": "HTML", "size": 2096 }, { "name": "CSS", "size": 2081 } ],
  "languageCount": 3,
  "topics": [ { "name": "chrome-extension", "stars": 43211 } ],
  "topicCount": 1,
  "diskUsageKb": 75,
  "pullRequests": 4,
  "issues": 12,
  "description": "Webextension to rewrite phrases in pages",
  "primaryLanguage": "JavaScript",
  "createdAt": "2015-03-14T22:35:11Z",
  "pushedAt": "2022-02-11T14:26:00Z",
  "defaultBranchCommitCount": 54,
  "license": null,
  "assignableUserCount": 1,
  "codeOfConduct": null,
  "forkingAllowed": true,
  "nameWithOwner": "pelmers/text-rewriter",
  "parent": null
}
```

## Algorithm
 1. Ignore repos that dont follow [requirements](#requirements)
 2. Extract [relevant data](#relevant-data)
 3. Embed using OpenAI embeddings
 4. DBSCAN clustering
 5. GPT label generation (categorization)

### Requirements
- `stars > 50`
- `archived = false`
- `createdAt > 1 month ago`

### Relevant Data
__Not for Recommendations__ (for url): `nameWithOwner`

__Embedded__: `name, topics.names, description, language.names`

__Not Embedded__: `stars (log scale), createdAt (convert to days since), pushedAt (convert to days since)`


