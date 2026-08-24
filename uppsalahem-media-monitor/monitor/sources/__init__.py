from .bing_news import fetch as fetch_bing_news
from .bluesky import fetch as fetch_bluesky
from .google_news import fetch as fetch_google_news
from .reddit import fetch as fetch_reddit
from .sr_uppland import fetch as fetch_sr_uppland
from .svt_uppsala import fetch as fetch_svt_uppsala

# Registret som main.py använder för att slå upp källor via namn.
SOURCE_REGISTRY = {
    "google_news": fetch_google_news,
    "bing_news": fetch_bing_news,
    "svt_uppsala": fetch_svt_uppsala,
    "sr_uppland": fetch_sr_uppland,
    "reddit": fetch_reddit,
    "bluesky": fetch_bluesky,
}

__all__ = ["SOURCE_REGISTRY"]
