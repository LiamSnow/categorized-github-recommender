# Categorized GitHub Recommender

The goal of this project is such that the user can sign into a website
using their GitHub account and be given recommendations for new
repositories they could explore based off their starred and created
repositories.

Different niches in repositories have different amounts
of relative stars, so our goal with this was to split up the
users interests into categories and give recommendation for
each category.

In order to achieve this we had to make a pre-processing step
to read of all the GitHub repositories and then categories
based of embedding similarity. This code is located inside
`preprocessor/` and has more information inside its README.

The code for recommendation, categorization of unknown
repositories (kNN), and the website is all located under
`website/`.
