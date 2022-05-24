import os
from dotenv import load_dotenv

load_dotenv()

TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")

BASE_URL = "https://api.twitter.com"

BASE_URL_1 = f"{BASE_URL}/1.1"

BASE_URL_2 = f"{BASE_URL}/2"
