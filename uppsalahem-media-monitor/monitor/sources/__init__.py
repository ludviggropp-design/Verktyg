from .google_news import fetch as fetch_google_news
from .reddit import fetch as fetch_reddit
from .bluesky import fetch as fetch_bluesky

# Registret som main.py använder för att slå upp källor via namn.
SOURCE_REGISTRY = {
    "google_news": fetch_google_news,
    "reddit": fetch_reddit,
    "bluesky": fetch_bluesky,
}

__all__ = ["SOURCE_REGISTRY"]
