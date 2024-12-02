
# load chroma db
# load .../preprocessor/data/final.sqlite
# load cache.sqlite

# CATEGORIZE
# takes: user's created and starred repos
# check which repos exist final.sqlite or cache.sqlite
# unknown repos:
    # embedding_text = f"{name} {description} {topics} {languages}"
    # make requests to openAI (watch for rate limits)
    # run kNN to categorize
    # save to cache.sqlite
# return map of categories (ID => {name, count})
 # where count is how many repos the user has in that repo

# RECOMMEND
# takes: user's created and starred repos
# call CATEGORIZE, take top 5 categories
# recommend using:
#  - not starred by user
#  - high star count
#  - recently pushed
#  - recently created
#
