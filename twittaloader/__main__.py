import sys
import requests
from tqdm import tqdm
from .auth import get_auth_headers
from .config import BASE_URL
from .log import logger


def main(tweet_id: str):
    res = requests.get(
        f"{BASE_URL}/tweets/{tweet_id}",
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
    urls: list[str] = [medium["url"] for medium in media]
    filenames = [url.split("/")[-1] for url in urls]
    for url, filename in tqdm(zip(tqdm(urls), filenames)):
        res = requests.get(url)
        with open(filename, "wb") as f:
            f.write(res.content)


if __name__ == "__main__":
    main(sys.argv[1])
