import json
from datetime import datetime
from getpass import getpass
from pathlib import Path

import requests
from tqdm import tqdm

from .config import BASE_URL_V2
from .log import logger


@logger.catch
class Twittaloader:
    config_location = Path.home() / ".twittaconfig"
    default_expansions = ["attachments.media_keys", "author_id"]
    default_media_fields = ["type", "url", "variants"]
    default_tweet_fields = ["created_at"]
    default_user_fields = ["username"]
    config = {}

    def __init__(self, *tweet_ids: str):
        self.tweet_ids = tweet_ids
        self.get_tokens()

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
            "expansions": ",".join(self.default_expansions),
            "media.fields": ",".join(self.default_media_fields),
            "tweet.fields": ",".join(self.default_tweet_fields),
            "user.fields": ",".join(self.default_tweet_fields),
        }

    def __call__(self):
        tweet_ids = self.tweet_ids
        if len(tweet_ids) == 1:
            res = requests.get(
                f"{BASE_URL_V2}/tweets/{tweet_ids[0]}",
                headers=self.get_auth_headers(),
                params=self.get_default_params(),
            )
            data = res.json()
            datetime_string = datetime.strptime(data["data"]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
        else:
            res = requests.get(
                f"{BASE_URL_V2}/tweets",
                headers=self.get_auth_headers(),
                params={
                    **self.get_default_params(),
                    "ids": ",".join(tweet_ids),
                },
            )
            data = res.json()
            datetime_string = datetime.strptime(data["data"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
        if not res.ok:
            return logger.error(f"{res.status_code}:\n{res.text}")

        media = data["includes"]["media"]
        users = data["includes"]["users"]
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