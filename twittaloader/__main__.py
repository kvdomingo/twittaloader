import sys
import json
import requests
from datetime import datetime
from getpass import getpass
from pathlib import Path
from tqdm import tqdm
from .config import BASE_URL_V1, BASE_URL_V2
from .log import logger


class Twittaloader:
    def __init__(self, tweet_id: str):
        self.config_location = Path.home() / ".twittaconfig"
        self.tweet_id = tweet_id
        self.config = {}
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

    def main(self):
        tweet_id = self.tweet_id
        res = requests.get(
            f"{BASE_URL_V1}/statuses/show.json",
            headers=self.get_auth_headers(),
            params={"id": tweet_id},
        )
        if not res.ok:
            return logger.error(f"{res.status_code}:\n{res.text}")
        data = res.json()
        user_handle = data["user"]["screen_name"]
        created = datetime.strptime(data["created_at"], "%a %b %d %H:%M:%S %z %Y")
        datetime_string = created.strftime("%Y-%m-%d_%H-%M-%S")
        if extended_entities := data.get("extended_entities"):
            media = extended_entities["media"]
            if video_info := media[0].get("video_info"):
                variants = video_info["variants"]
                bitrates = [variant.get("bitrate", 0) for variant in variants]
                max_bitrate = max(bitrates)
                max_bitrate_index = bitrates.index(max_bitrate)
                max_bitrate_url = variants[max_bitrate_index]["url"]
                extension = variants[max_bitrate_index]["content_type"].split("/")[-1]
                filename = f"{user_handle}-{datetime_string}.{extension}"
                res = requests.get(max_bitrate_url)
                with open(filename, "wb") as f:
                    f.write(res.content)
            else:
                urls: list[str] = [medium["media_url_https"] for medium in media]
                for i, url in enumerate(tqdm(urls)):
                    extension = url.split("/")[-1].split(".")[-1]
                    filename = f"{user_handle}-{datetime_string}_{i + 1}.{extension}"
                    res = requests.get(url)
                    with open(filename, "wb") as f:
                        f.write(res.content)
        else:
            res = requests.get(
                f"{BASE_URL_V2}/tweets/{tweet_id}",
                headers=self.get_auth_headers(),
                params={
                    "expansions": "attachments.media_keys",
                    "media.fields": "url",
                },
            )
            if not res.ok:
                return logger.error(f"{res.status_code}:\n{res.text}")
            data = res.json()
            media = data["includes"]["media"]
            urls = [medium["url"] for medium in media]
            for i, url in enumerate(tqdm(urls)):
                extension = url.split(".")[-1]
                filename = f"{user_handle}-{datetime_string}_{i + 1}.{extension}"
                bare_url = ".".join(url.split(".")[:-1])
                res = requests.get(
                    bare_url,
                    params={
                        "format": extension,
                        "name": "orig",
                    },
                )
                with open(filename, "wb") as f:
                    f.write(res.content)


if __name__ == "__main__":
    Twittaloader(sys.argv[1]).main()
