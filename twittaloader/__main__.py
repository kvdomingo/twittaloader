import sys
import requests
from datetime import datetime
from tqdm import tqdm
from .auth import get_auth_headers
from .config import BASE_URL_1, BASE_URL_2
from .log import logger


def main(tweet_id: str):
    res = requests.get(
        f"{BASE_URL_1}/statuses/show.json",
        headers=get_auth_headers(),
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
            f"{BASE_URL_2}/tweets/{tweet_id}",
            headers=get_auth_headers(),
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
    main(sys.argv[1])
