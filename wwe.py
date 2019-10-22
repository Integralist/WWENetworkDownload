#!/usr/bin/python3

# standard library modules

import sys
from typing import Dict, Tuple, Union

# third party modules

import arrow

import requests

# constants

HEADERS = {"User-Agent": "okhttp/3.12.1"}

REALM_HEADERS = {
    "x-api-key": "640a69fb-68b1-472c-ba4b-36f50288c984",
    "realm": "dce.wwe",
}

DICE_MOBILE_API_KEY = "640a69fb-68b1-472c-ba4b-36f50288c984"


class Episode:
    """Create instance of a episode video type."""

    def __init__(self, entry: Dict):
        self.entry = entry

    def filename(self) -> str:
        ep_num = self.entry["episodeNumber"]

        if self.entry["episodeNumber"] < 10:
            ep_num = "0" + str(self.entry["episodeNumber"])

        file_date = arrow.get(
            self.entry["firstBroadcastDate"], "YYYY-MM-DDTHH:mm:ssZ"
        ).format("M-DD-YYYY")

        file_name = "{} {} - S{}E{} - {}".format(
            self.entry["customFields"]["Franchise"],
            self.entry["episodeName"],
            self.entry["releaseYear"],
            ep_num,
            file_date,
        )

        return file_name


class PPV:
    """Create instance of a pay-per-view video type."""

    def __init__(self, entry: Dict):
        self.entry = entry

    def filename(self) -> str:
        # Since we have a PPV get the title and year into variables
        ppv_title = self.entry["episodeName"]
        ppv_year = self.entry["releaseYear"]

        # Check if the PPV already has the year in it.
        # For example "This Tuesday in Texas 1991" has the year,
        # but "WrestleMania 35" doesn't.
        # Since we don't want to have "This Tuesday in Texas 1991 1991" as
        # our filename we will just use the PPV title
        if str(ppv_year) in ppv_title:
            file_name = "{} {}".format(
                self.entry["customFields"]["Franchise"],
                self.entry["episodeName"],
            )
        else:
            file_name = "{} {} {}".format(
                self.entry["customFields"]["Franchise"],
                self.entry["episodeName"],
                self.entry["releaseYear"],
            )

        return file_name


class Generic:
    """Create instance of a generic video type."""

    def __init__(self, entry: Dict):
        self.entry = entry

    def filename(self) -> str:
        if not self.entry.get("title"):
            raise Exception("don't recognize this event type")

        # TODO: use normalize_title rather than doing this here
        file_name = (
            self.entry["title"]
            .replace(" ", "_")
            .replace("&", "and")
            .replace(":", "-")
        )

        return file_name


class Network:
    def __init__(self, user: str, password: str):
        with requests.Session() as self._session:
            self._session.headers.update(HEADERS)

        self.user = user
        self.password = password
        self.logged_in = False

    def _update_session(self, auth_token: str):
        """Updates logged-in session to include 'access' token."""

        if not auth_token:
            print("No access token found.")
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

        return video_url["playerUrlCallback"]

    def _episode_factory(self, entry: Dict) -> Union[Episode, PPV, Generic]:
        if entry["customFields"].get("EventStyle") == "Episodic":
            return Episode(entry)
        elif entry["customFields"].get("EventStyle") == "PPV":
            return PPV(entry)
        else:
            return Generic(entry)

    def get_video_info(self, link: str) -> Tuple[str, str]:
        """Returns video stream url and video title."""

        api_link = self._session.get(
            "https://cdn.watch.wwe.com/api/page?path={}".format(link)
        ).json()

        entry = api_link["entries"][0]["item"]

        episode = self._episode_factory(entry)
        episode.filename()

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
