import argparse
import math
import multiprocessing
import os
import subprocess
import sys
from typing import Dict, List, Tuple

import wwe

# constants

CORES = multiprocessing.cpu_count()
CHUNK = round(CORES / 2)

# globals

episode_count = 0


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

    return episodes


def generate_ffmpeg_command(
    episode: str, network: wwe.Network, flags: argparse.Namespace
) -> str:
    global episode_count
    episode_count += 1

    video_info, title = network.get_video_info(episode)
    stream_url = network.hls_url(video_info)
    user_agent = "WWE/4.0.13 (Linux;Android 9) ExoPlayerLib/2.9.3"

    if flags.index:
        title = f"{episode_count}. {title}"

    directory = ""
    if flags.output:
        directory = flags.output

    # generate ffmpeg command to download the video via the stream URL
    ffmpeg_command = (
        f'ffmpeg -user_agent "{user_agent}" -i "'
        + stream_url
        + '" -c copy '
        + f"'{directory}{title}"
        + ".mp4' -y"
    )

    return ffmpeg_command


def process(episodes: List[str], flags: argparse.Namespace):
    """Authenticate user, acquire video stream, download video(s).

    Utilizes basic chunking algorithm to prevent abusing CPU.
    """
    output: Dict[str, int] = {}
    if not flags.verbose:
        output = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

    network = wwe.Network(user, password, flags)
    network.login()
    print("\nAuthenticated successfully.\n")

    # TODO: maybe refactor the following logic to use proper pooling algorithm
    # as implemented by concurrent.futures.ProcessPoolExecutor

    print(f"Number of videos: {len(episodes)}.")

    divider = CHUNK

    start = 0
    for n in range(0, CHUNK):
        chunk = math.ceil(len(episodes) / divider)

        if len(episodes) <= divider:
            # reduce the divider to prevent using too few cores
            chunk = len(episodes)

        end = start + chunk

        try:
            processes = []

            for i in range(start, end):
                cmd = generate_ffmpeg_command(episodes[i], network, flags)

                if flags.debug:
                    processes.append(cmd)
                else:
                    # run the shell command directly via the /bin/sh executable
                    # and do it in a subprocess for the purposes of parallelism
                    p = subprocess.Popen(  # type: ignore
                        cmd, shell=True, **output
                    )
                    processes.append(p)  # type: ignore

            if flags.speak:
                subprocess.call(
                    "say new batch of subprocesses starting", shell=True
                )

            print(f"\nGenerated subprocesses: {chunk}.")
            print("Waiting for subprocesses to complete.")

            for p in processes:  # type: ignore
                if flags.debug:
                    print("\n", p)
                else:
                    p.communicate()

        except IndexError:
            # account for uneven lists of files where we generate a partial
            # list of processes but then get an error from referencing an
            # index that doesn't exist. this allows us to complete the
            # download for that partial list of processes.
            if len(processes) > 0:
                print(f"\nGenerated subprocesses: {len(processes)}.")
                print("Waiting for subprocesses to complete.")
                for p in processes:  # type: ignore
                    if flags.debug:
                        print("\n", p)
                    else:
                        p.communicate()

        start = end

    if flags.speak:
        subprocess.call("say finished processing", shell=True)
    print("\nfinished downloading.")


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
        "-d", "--debug", help="Dry-run displays ffmpeg commands.", type=bool
    )
    parser.add_argument(
        "-v", "--verbose", help="Verbose prints ffmpeg output.", type=bool
    )
    parser.add_argument(
        "-i", "--index", help="Index adds indices to filenames.", type=bool
    )
    parser.add_argument(
        "-s", "--speak", help="Use `say` binary for alerts.", type=bool
    )
    parser.add_argument(
        "-o", "--output", help="Directory to place files into.", default=None
    )

    return parser.parse_args()


flags = parse_flags()
user, password = credentials(flags.user, flags.password)
episodes = normalize_links(flags)

try:
    process(episodes, flags)
except Exception as err:
    print(err)
