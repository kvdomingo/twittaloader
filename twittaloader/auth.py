from .config import TWITTER_BEARER_TOKEN


def get_auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
    }
