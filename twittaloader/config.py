import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")

BASE_URL = "https://api.twitter.com/2"
