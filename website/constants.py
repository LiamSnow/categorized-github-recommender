from dotenv import load_dotenv
import os

load_dotenv()

embeddings_db = '../preprocessor/output/embeddings/'

meta_db = '../preprocessor/output/meta.sqlite'

cache_db = 'cache.sqlite'
domain = os.getenv('FLASK_DOMAIN')

# how many recommendations per category
num_recommendations = 4

# how many categories to give recommendations for
num_categories = 8
