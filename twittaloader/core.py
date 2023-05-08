import json
import re
import urllib.parse
from getpass import getpass
from pathlib import Path
from typing import Iterable

import requests
import tweepy
from tqdm import tqdm

from .log import logger

NUMERIC_RE = re.compile(r"^\d+$", re.I)


@logger.catch
class Twittaloader:
    config_location = Path.home() / ".twittaconfig"
    default_expansions = ["attachments.media_keys", "author_id"]
    default_media_fields = ["type", "url", "variants"]
    default_tweet_fields = ["created_at"]
    default_user_fields = ["username"]
    config = {}

    def __init__(self, *tweet_args: str):
        if len(tweet_args) == 0:
            raise ValueError("Missing args")
        self.tweet_ids = self.parse_tweet_args(tweet_args)
        self.get_tokens()
        self.client = tweepy.Client(self.config["TWITTER_BEARER_TOKEN"])

    @staticmethod
    def parse_tweet_args(tweet_args: Iterable[str]) -> list[str]:
        def _func(arg):
            if re.match(NUMERIC_RE, arg):
                return arg
            elif arg.startswith("https://"):
                pr = urllib.parse.urlparse(arg)
                id_: str = pr.path.split("/")[-1]
                return id_
            else:
                raise ValueError(f"Unrecognized format: {arg}")

        parsed = list(map(_func, tweet_args))
        return parsed

    def get_tokens(self):
        if not self.config_location.exists():
            return self.setup()
        with open(self.config_location, "r") as f:
            self.config = json.load(f)

    def setup(self):
        logger.info("\nTwittaloader first time setup. Please provide the following:\n")
        config = {"TWITTER_BEARER_TOKEN": getpass("Twitter API Bearer token: ")}
        with open(self.config_location, "w+") as f:
            json.dump(config, f)
        self.config = config

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.config['TWITTER_BEARER_TOKEN']}"}

    def get_default_params(self):
        return {
            "expansions": self.default_expansions,
            "media_fields": self.default_media_fields,
            "tweet_fields": self.default_tweet_fields,
            "user_fields": self.default_user_fields,
        }

    def __call__(self):
        tweet_ids = self.tweet_ids
        if len(tweet_ids) == 1:
            res = self.client.get_tweet(tweet_ids[0], **self.get_default_params())
            data = res.data
            datetime_string = data["created_at"].strftime("%Y-%m-%d_%H-%M-%S")
        else:
            res = self.client.get_tweets(tweet_ids, **self.get_default_params())
            data = res.data
            datetime_string = data[0]["created_at"].strftime("%Y-%m-%d_%H-%M-%S")

        media = res.includes["media"]
        users = res.includes["users"]
        user_handle = users[0]["username"]

        for i, medium in enumerate(tqdm(media)):
            filename = f"{user_handle}-{datetime_string}_{i + 1}"
            match medium["type"]:
                case "photo":
                    url = medium["url"]
                    extension = url.split(".")[-1]
                    url_no_extension = ".".join(url.split(".")[:-1])
                    res = requests.get(
                        url_no_extension,
                        params={
                            "format": extension,
                            "name": "orig",
                        },
                    )
                case "video":
                    variants = medium["variants"]
                    bitrates = [v.get("bit_rate") or 0 for v in variants]
                    index_highest_bitrate = bitrates.index(max(bitrates))
                    selected_variant = variants[index_highest_bitrate]
                    url = selected_variant["url"]
                    extension = "mp4"
                    res = requests.get(url)
                case "animated_gif":
                    url = medium["variants"][0]["url"]
                    extension = "mp4"
                    res = requests.get(url)
                case _:
                    logger.warning(f"Unknown type `{medium['type']}`")
                    continue
            if res.ok:
                with open(f"{filename}.{extension}", "wb") as f:
                    for chunk in res.iter_content(chunk_size=1024):
                        f.write(chunk)
