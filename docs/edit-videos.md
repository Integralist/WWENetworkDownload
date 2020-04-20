## Edit Videos By Time Segments

If you don't want the full video you download (e.g. maybe there are only a couple of matches you're interested in), then you can edit the video and generate a new video file that consists of only the content you're interested in.

This is done using the `ffmpeg` command line tool.

The command you need to generate can be long and complex so I wrote a Python script to generate it for you based upon time 'segments' put into a `segments.txt` file.

> Note: the actual _execution_ of the script is also _very slow_ because you're streaming the video from WWE servers through ffmpeg.

If you're interested in what the raw ffmpeg command would look like, then below is an example:

```bash
ffmpeg -i 1986.10.21\ -\ WWE\ S1986E41\ \(Prime\ Time\ Wrestling\).mp4 -to 00:02:04 0.mp4 -ss 00:13:56  -to 00:15:28 1.mp4 -ss 00:21:40  -to 00:22:24 2.mp4 -ss 00:27:31  -to 00:28:33 3.mp4 -ss 00:30:40  -to 00:31:12 4.mp4 -ss 00:37:10  -to 00:39:08 5.mp4 -ss 00:44:39  -to 00:45:22 6.mp4 -ss 00:50:30  -to 00:51:37 7.mp4 -ss 00:53:45 8.mp4 && printf "file '0.mp4'\nfile '1.mp4'\nfile '2.mp4'\nfile '3.mp4'\nfile '4.mp4'\nfile '5.mp4'\nfile '6.mp4'\nfile '7.mp4'\nfile '8.mp4'" > concat.txt && ffmpeg -f concat -safe 0 -i concat.txt -c copy 1986.10.21.mp4 && rm {0,1,2,3,4,5,6,7,8}.mp4 && rm concat.txt && say all done
```

...wowza. yeah.

My automated process requires two files:

1. a `segments.txt` file for storing time segments for each video you want to edit.
2. a Python script for extracting the time segments and generating an ffmpeg command.

## Usage

Let's start with the 'usage' example and then I'll show you the segments file and the Python script.

```bash
$ python3 gen.py --help

usage: python gen.py --path <path/to/drive/where/its/subdirectories/are/years/>

WWE Video Editor

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  path to external drive. note: the video files should
                        be stored within subdirectories of the specified path,
                        while the subdirectories should be categoried by the
                        year of the video. e.g. set path to
                        /Volumes/external_drive/videos/wwf/ and it'll look for
                        videos based on the filenames in the segments.txt.
                        meaning a title of '1999.01.24 - Royal Rumble 1999'
                        would cause the tool to lookup the video in the /1999/
                        directory.
```

## Segments File

The `segments.txt` file should be in the same directory as the script, and its content should look something like the following:

```
1987.04.06 - WWE S1987E14 (Prime Time Wrestling)

00:02:19
00:08:28 00:32:26
00:34:40 00:35:42
00:40:31 00:42:57
00:47:56 00:49:06
00:51:07

1987.04.13 - WWE S1987E15 (Prime Time Wrestling)

00:39:50
00:45:39 00:47:33
00:56:44 00:57:35
01:06:48 01:08:36
01:17:37
```

Notice the first and last lines of each video's time segments don't have two time segments defined. e.g. for the first video `1987.04.06 - WWE S1987E14 (Prime Time Wrestling)` we have the first line set to just `00:02:19` and the last line of those time segments set to `00:51:07` while all other time segments inbetween them are comprised of _two_ time segments: a _start_ and a _stop_ time.

This is because the first line is saying we want our first video segment to be from the beginning of the video _until_ 2mins 19secs into the video. 

The last line tells us we want our final segment to start 1hr 17mins 37secs into the video and to continue until the end of the video.

## Python Script

Here is the Python script:

```python
import argparse
import subprocess


def extract_episodes():
    """generates data structure containing videos with their time segments.

    output will resemble:

    {
        "video_title_A": [
            [00:02:16],
            [00:10:00, 00:20:00],
            [00:30:00, 00:40:00],
            ...
        ]
        "video_title_B": [
            [00:02:16],
            [00:10:00, 00:20:00],
            [00:30:00, 00:40:00],
            ...
        ]
    }
    """

    episodes = {}
    title = ""  # will be updated on every loop iteration

    with open("segments.txt") as f:
        for i, line in enumerate(f):
            no_linebreak = line.splitlines()[0]
            start_finish = no_linebreak.split(" ")

            if len(start_finish) > 2:
                title = no_linebreak
                episodes[title] = []
            elif (
                len(start_finish) == 0
                or len(start_finish) == 1
                and start_finish[0] == ""
            ):
                # we've found an empty line (used as a visual separator)
                continue
            else:
                # we've reached the 'time segment' of the listed video
                episodes[title].append(start_finish)

    return episodes


def parse_segments(episodes):
    for title, segments in episodes.items():
        tmp = []

        for file_number, segment in enumerate(segments):
            for i, time in enumerate(segment):
                num_segments = len(segment)

                # segments [
                #   segment [i=0 '00:10:00'],
                #   segment [i=0 '00:15:02', i=1 '00:16:00'],
                #   segment [i=0' 00:23:37', i=1 '00:34:14'],
                #   segment [i=0' 00:35:40', i=1 '00:37:07'],
                #   segment [i=0' 00:44:40', i=1 '00:45:30'],
                #   segment [i=0' 00:50:46', i=1 '00:52:44'],
                #   segment [i=0' 01:02:34', i=1 '01:03:19'],
                #   segment [i=0' 01:14:02']
                # ]

                # if the first line only has a single value
                if file_number == 0 and num_segments == 1:
                    flag = "-to"
                # if the last segment line only has a single value
                elif file_number == len(segments) - 1 and num_segments == 1:
                    flag = "-ss"
                else:
                    flag = "-ss" if i == 0 else "-to"

                file = (
                    "" if num_segments > 1 and i == 0 else f"{file_number}.mp4"
                )
                tmp.append(f"{flag} {time} {file}")

                # we mutate the original episodes data structure so that the
                # nested lists of time segments becomes one long string of
                # ffmpeg flags.
                #
                # e.g. "-to 00:02:16 1.mp4 -ss 00:10:00 -to 00:20:00 2.mp4"
                episodes[title] = " ".join(tmp)

    return episodes


def normalize_video_filename(video):
    replacements = {"(": r"\(", ")": r"\)", " ": r"\ "}
    return "".join([replacements.get(c, c) for c in video])


def generate_tmp_video_files(num_files):
    tmp_video_files = []

    for i in range(num_files):
        linebreak = "" if i == num_files - 1 else "\\n"
        tmp_video_files.append(f"file '{i}.mp4'{linebreak}")

    return "".join(tmp_video_files)


def generate_rm_of_tmp_video_files(num_files):
    rm_video_files = []

    for i in range(num_files):
        comma = "" if i == num_files - 1 else ","
        rm_video_files.append(f"{i}{comma}")

    return "{" + "".join(rm_video_files) + "}"


def main(args: argparse.Namespace):
    output_dir = normalize_video_filename(args.path)

    episodes = parse_segments(extract_episodes())

    for episode, flags in episodes.items():
        video = normalize_video_filename(episode)
        video_name = normalize_video_filename(episode.split("- ")[1])
        video_date = episode.split(" ")[0]
        year = video_date.split(".")[0]

        # sometimes I put in a new title but then stop before I start entering more
        # time segments for that video (just so I know where to start back up.
        # to avoid that scenario from breaking this code and causing an exception,
        # I'll just skip over any video that's missing segments.
        if flags == []:
            continue

        num_files = len(flags.split(".mp4")) - 1

        cmd_extract = f"ffmpeg -i {video}.mp4 {flags}"
        cmd_temp = f'printf "{generate_tmp_video_files(num_files)}" > concat.txt'
        cmd_concat = (
            f"ffmpeg -f concat -safe 0 -i concat.txt -c copy {video_date}-{video_name}-edit.mp4"
        )
        cmd_rm = (
            f"rm {generate_rm_of_tmp_video_files(num_files)}.mp4 && rm concat.txt"
        )
        cmd_done = "say all done"

        cmd_cd = f"cd {output_dir}{year}"

        command = f"{cmd_cd} && {cmd_extract} && {cmd_temp} && {cmd_concat} && {cmd_rm} && {cmd_done}"  # noqa

        # synchronously execute ffmpeg (i.e. blocking operation)
        #
        # change to `p = subprocess.Pcall` instead of just `.call` and then use the
        # `p.communicate()` to co-ordinate multiple subprocesses.
        subprocess.call(command, shell=True)


parser = argparse.ArgumentParser(
    description="WWE Video Editor",
    usage="python gen.py --path <path/to/drive/where/its/subdirectories/are/years/>")

path_help = """path to external drive.
note: the video files should be stored within subdirectories of the specified
path, while the subdirectories should be categoried by the year of the video.
e.g. set path to /Volumes/external_drive/videos/wwf/ and it'll look for videos
based on the filenames in the segments.txt. meaning a title of '1999.01.24 -
Royal Rumble 1999' would cause the tool to lookup the video in the /1999/
directory.
"""

parser.add_argument('-p', '--path', required=True, help=path_help)

args = parser.parse_args()

main(args)
```

### What does this script do?

This script does multiple things:

- it generates multiple smaller videos based upon your time segments.
- it generates a `concat.txt` file that lists these smaller video files.
- it uses the `concat.txt` file to generate a new video consisting of those smaller video segments.
- it cleans-up the `concat.txt` file and all the smaller video files.

This leaves you with two videos:

1. the original video
2. the new 'shorter' (i.e. edited) video

The Python script expects you to have subdirectories within the directory you specified as the `--path` value. These subdirectories map to the year of the videos listed in the `segments.txt`. So in the example `segments.txt` file above we have two videos dated from 1987 which means in our output directory we need to make sure there is a folder called `1987` that contains that listed video.
