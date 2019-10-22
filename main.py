# standard library modules

import argparse
import os
import subprocess
import sys
from typing import List, Tuple

# application modules

import wwe


def normalize_filename(f: str) -> str:
    """Replaces non-alphanumerical characters within a given filename."""

    def safe_char(c):
        if c.isalnum():
            return c
        else:
            return "_"

    return "".join(safe_char(c) for c in f).rstrip("_")


def credentials(user: str, password: str) -> Tuple[str, str]:
    """Extracts credentials from either CLI flags or environment variables."""

    if not user and not password:
        try:
            user = os.environ["WWE_USER"]
            password = os.environ["WWE_PASS"]
        except KeyError as e:
            msg = "Provide credentials via command line\nor environment vars:"
            env_vars = "WWE_USER, WWE_PASS"
            example_env = (
                "export WWE_USER=foo WWE_PASS=bar && python3 main.py -l <url>"
            )
            example_flags = "python3 main.py -u <user> -p <password> -l <url>"
            examples = f"Examples:\n\t{example_env}\n\t{example_flags}"
            error = "MISSING ENV VAR(S)"
            print(f"\n{error} {e}.\n\n{msg} {env_vars}\n\n{examples}")
            sys.exit(1)

    return user, password


def normalize_links(flags: argparse.Namespace) -> List[str]:
    """Normalize the link provided by the user.

    Multiple formats are supported:

    - FQD (fully qualified domain)
    - URL Path (with or without a slash prefix)

    Ultimately we want a URL path with a slash prefix.

    Examples:
        https://watch.wwe.com/episode/foo/bar > /episode/foo/bar
        /episode/foo/bar                      > /episode/foo/bar
        episode/foo/bar                       > /episode/foo/bar

    If not using --link, then check --flags. To account for both approaches
    we'll return a list of normalized episodes. This means if the user is using
    the --link flag (for a single video download) we'll wrap it in a list too.
    """

    episode = flags.link
    episodes = [episode]

    if not episode and not flags.files:
        print("\nMISSING VIDEO URL(S), see: --link, --files")
        sys.exit(1)

    if not episode and flags.files:
        episodes = []
        with open(flags.files) as f:
            for _, line in enumerate(f):
                no_linebreak = line.splitlines()[0]
                episodes.append(no_linebreak)

    for i, ep in enumerate(episodes):
        wwe_domain = "https://watch.wwe.com/"
        if ep.startswith(wwe_domain):
            ep = ep.replace(wwe_domain, "")

        # e = episode
        # p = program
        # o = original
        if ep.startswith("e") or ep.startswith("p") or ep.startswith("o"):
            ep = "/" + ep

        episodes[i] = ep

    # TODO: don't iterate twice but pass direct to singular process()
    return episodes


def process(episodes: List[str], debug: bool):
    """Authenticate user, acquire video stream, generate ffmpeg command."""

    network = wwe.Network(user, password)
    network.login()
    print("authenticated successfully")

    processes = []

    for i, episode in enumerate(episodes):
        video_info, title = network.get_video_info(episode)
        stream_url = network.hls_url(video_info)
        user_agent = "WWE/4.0.13 (Linux;Android 9) ExoPlayerLib/2.9.3"

        # generate ffmpeg command to download the video via the stream URL
        ffmpeg_command = (
            f'ffmpeg -user_agent "{user_agent}" -i "'
            + stream_url
            + '" -c copy '
            + normalize_filename(title)
            + ".mp4 -y"
        )

        print(f"about to download video: {title}")

        if not debug:
            # run the shell command directly via the /bin/sh executable
            # and do it in a subprocess for the purposes of parallelism.
            process = subprocess.Popen(
                ffmpeg_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
        else:
            print(ffmpeg_command)

    print(f"wait for {len(episodes)} processes to finish.")

    for process in processes:
        process.communicate()

    print("all done!")


def parse_flags() -> argparse.Namespace:
    """Parse CLI flags provided by user."""

    parser = argparse.ArgumentParser(
        description="Download videos from the WWE Network"
    )
    parser.add_argument(
        "-u", "--user", help="WWE Network user account.", default=None
    )
    parser.add_argument(
        "-p", "--password", help="WWE Network account password.", default=None
    )
    parser.add_argument(
        "-l", "--link", help="Video link to download.", default=None
    )
    parser.add_argument(
        "-f", "--files", help="File with list of links", default=None
    )
    parser.add_argument(
        "-d", "--debug", help="Dry-run.", type=bool, default=False
    )

    return parser.parse_args()


flags = parse_flags()
user, password = credentials(flags.user, flags.password)
episodes = normalize_links(flags)
process(episodes, flags.debug)
