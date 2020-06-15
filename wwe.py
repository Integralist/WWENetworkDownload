#!/usr/bin/python3

import argparse
import subprocess
import sys
import time
from typing import Dict, Tuple, Union

import requests

# constants

HEADERS = {"User-Agent": "okhttp/3.12.1"}

REALM_HEADERS = {
    "x-api-key": "640a69fb-68b1-472c-ba4b-36f50288c984",
    "realm": "dce.wwe",
}


def normalize_filename(f: str) -> str:
    """Replaces non-alphanumerical characters within a given filename."""

    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"

    return "".join(safe_char(c) for c in f).rstrip("_")


class Episode:
    """Create instance of a episode video type."""

    def __init__(self, entry: Dict):
        self.entry = entry

    def filename(self) -> str:
        organization = self.entry["customFields"]["Franchise"]
        episode_num = self.entry["episodeNumber"]
        normalized_num = (
            "0" + str(episode_num) if episode_num < 10 else episode_num
        )
        episode_title = self.entry["episodeName"]
        series_year = self.entry["releaseYear"]
        broadcast = self.entry["firstBroadcastDate"]
        parsed_date = time.strptime(broadcast, "%Y-%m-%dT%H:%M:%SZ")
        formatted_date = time.strftime("%Y.%m.%d", parsed_date)

        file_name = f"{formatted_date} - {organization} S{series_year}E{normalized_num} ({episode_title})"  # noqa

        return file_name


class PPV:
    """Create instance of a pay-per-view video type."""

    def __init__(self, entry: Dict):
        self.entry = entry

    def filename(self) -> str:
        organization = self.entry["customFields"]["Franchise"]
        broadcast = self.entry["firstBroadcastDate"]
        parsed_date = time.strptime(broadcast, "%Y-%m-%dT%H:%M:%SZ")
        formatted_date = time.strftime("%Y.%m.%d", parsed_date)

        # because the ffmpeg command we generate uses single quotes, we need to
        # be sure that our title doesn't include them.
        ppv_title = self.entry["episodeName"].replace("'", "_")

        ppv_year = self.entry["releaseYear"]

        # Check if the PPV already has the year in it.
        #
        # e.g. "This Tuesday in Texas 1991" or "Hardcore Heaven 1995".
        #
        # If it does, then we don't add the year to the title.
        year = f" ({ppv_year})" if str(ppv_year) not in ppv_title else ""

        file_name = f"{formatted_date} - {organization} {ppv_title}{year}"

        return file_name


class Generic:
    """Create instance of a generic video type."""

    def __init__(self, entry: Dict, flags: argparse.Namespace):
        self.entry = entry
        self.flags = flags

    def filename(self) -> str:
        if not self.entry.get("title"):
            msg = "don't recognize this event type"

            if self.flags.speak:
                subprocess.call(f"say error {msg}", shell=True)

            raise Exception(msg)

        # the ffmpeg command we generate uses single quotes, so we need to make
        # sure we remove any single quotes from the video's title.
        title = self.entry["title"].replace("'", "")

        broadcast = self.entry.get("firstBroadcastDate")

        if broadcast:
            parsed_date = time.strptime(broadcast, "%Y-%m-%dT%H:%M:%SZ")
            formatted_date = time.strftime("%Y.%m.%d", parsed_date)
            title = f"{formatted_date} - {title}"

        return title


class Network:
    def __init__(self, user: str, password: str, flags: argparse.Namespace):
        with requests.Session() as self._session:
            self._session.headers.update(HEADERS)

        self.user = user
        self.password = password
        self.logged_in = False
        self.flags = flags

    def _update_session(self, auth_token: str):
        """Updates logged-in session to include 'access' token."""

        if not auth_token:
            msg = "No access token found."
            print(msg)

            if self.flags.speak:
                subprocess.call(f"say error {msg}", shell=True)

            sys.exit(1)

        self._session.headers.update({"Authorization": f"Bearer {auth_token}"})
        self.logged_in = True

    def login(self):
        """Authenticate user credentials."""

        payload = {"id": self.user, "secret": self.password}

        token_data = self._session.post(
            "https://dce-frontoffice.imggaming.com/api/v2/login",
            json=payload,
            headers=REALM_HEADERS,
        ).json()

        if "code" in token_data:
            print(f'ERROR: {token_data.get("messages")}')

            if self.flags.speak:
                subprocess.call(
                    f'say error {token_data.get("messages")}', shell=True
                )

            sys.exit(1)

        auth_token = token_data.get("authorisationToken")
        self._update_session(auth_token)

    def _video_url(self, video_id: str) -> str:
        """Acquire video stream URL."""

        host = "dce-frontoffice.imggaming.com"
        path = "/api/v2/stream/vod/"

        video_url = self._session.get(
            f"https://{host}{path}{video_id}", headers=REALM_HEADERS
        ).json()

        stream_url = video_url.get("playerUrlCallback")

        if not stream_url:
            msg = "failed to acquire stream URL"

            if self.flags.speak:
                subprocess.call(f"say {msg}", shell=True)

            raise Exception(f"\nuh-oh! {msg}:\n\n{video_url}")

        return stream_url

    def _episode_factory(self, entry: Dict) -> Union[Episode, PPV, Generic]:
        if entry["customFields"].get("EventStyle") == "Episodic":
            return Episode(entry)
        elif entry["customFields"].get("EventStyle") == "PPV":
            return PPV(entry)
        else:
            return Generic(entry, self.flags)

    def get_video_info(self, link: str) -> Tuple[str, str]:
        """Returns video stream url and video title."""
        resp = self._session.get(
            "https://cdn.watch.wwe.com/api/page?path={}".format(link)
        )

        api_link = resp.json()

        if resp.status_code != 200:
            raise Exception(f"\nuh-oh! {link}: {resp.json()}")

        entry = api_link["entries"][0]["item"]

        episode = self._episode_factory(entry)

        return (
            self._video_url(
                api_link["entries"][0]["item"]["customFields"]["DiceVideoId"]
            ),
            episode.filename(),
        )

    def hls_url(self, video_info: str) -> str:
        """Extract HLS video URL from video data file."""

        stream = self._session.get(video_info, headers=REALM_HEADERS).json()

        return stream["hls"]["url"]
