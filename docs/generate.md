## Command Generation

If you don't want the full video you download (e.g. maybe there are only a couple of matches you're interested in), then you can edit the video and generate a new video file that consists of only the content you're interested in.

This is done using the `ffmpeg` command line tool.

The command you need to generate can be long and complex so I wrote a Python script to generate it for you based upon time 'segments' put into a `segments.txt` file.

### Script to generate ffmpeg command

Below is the Python3 script:

```python
import sys


def normalize_video_filename(video):
    replacements = {"(": r"\(", ")": r"\)", " ": r"\ "}
    return "".join([replacements.get(c, c) for c in video])


def extract_segments(num_lines):
    segments = []

    with open("segments.txt") as f:
        for i, line in enumerate(f):
            no_linebreak = line.splitlines()[0]
            start_finish = no_linebreak.split(" ")

            for j, segment in enumerate(start_finish):
                # if the first line only has a single value
                if i == 0 and len(start_finish) == 1:
                    flag = "-to"
                # if the last line only has a single value
                elif i == num_lines - 1 and len(start_finish) == 1:
                    flag = "-ss"
                else:
                    flag = "-ss" if j == 0 else "-to"
                file = "" if len(start_finish) > 1 and j == 0 else f"{i}.mp4"
                segments.append(f"{flag} {segment} {file}")

    return " ".join(segments)


def generate_tmp_video_files(num_lines):
    tmp_video_files = []

    for i in range(num_lines):
        linebreak = "" if i == num_lines - 1 else "\\n"
        tmp_video_files.append(f"file '{i}.mp4'{linebreak}")

    return "".join(tmp_video_files)


def generate_rm_of_tmp_video_files(num_lines):
    rm_video_files = []

    for i in range(num_lines):
        comma = "" if i == num_lines - 1 else ","
        rm_video_files.append(f"{i}{comma}")

    return "{" + "".join(rm_video_files) + "}"


num_lines = sum(1 for line in open("segments.txt"))

args = sys.argv[1:]

video = normalize_video_filename(args[0])
video_date = args[0].split(" ")[0]

cmd_extract = f"ffmpeg -i {video}.mp4 {extract_segments(num_lines)}"
cmd_temp = f'printf "{generate_tmp_video_files(num_lines)}" > concat.txt'
cmd_concat = f"ffmpeg -f concat -safe 0 -i concat.txt -c copy {video_date}.mp4"
cmd_rm = f"rm {generate_rm_of_tmp_video_files(num_lines)}.mp4 && rm concat.txt"
cmd_done = "say all done"

command = (
    f"{cmd_extract} && {cmd_temp} && {cmd_concat} && {cmd_rm} && {cmd_done}"
)

print(command)
```

### Script requirements

This script requires a `segments.txt` file in the same directory as the script, and its content should look something like the following:

```
00:02:04
00:13:56 00:15:28
00:21:40 00:22:24
00:27:31 00:28:33
00:30:40 00:31:12
00:37:10 00:39:08
00:44:39 00:45:22
00:50:30 00:51:37
00:53:45
```

Notice the first and last line don't have two time segments defined. 

The first line is saying we want our first video segment to be from the beginning of the video _until_ 2mins 4secs into the video. 

The last line tells us we want our final segment to start 53mins 45secs into the video and to continue until the end of the video.

### Executing the script

You would call it like so:

```bash
python3 gen.py "1986.10.21 - WWE S1986E41 (Prime Time Wrestling)"
```

> Note: the string provided as an argument to `gen.py` is the title the video downloader command line tool generates.

### Script output

Calling the Python3 script (as shown above) would produce the following output:

```bash
ffmpeg -i 1986.10.21\ -\ WWE\ S1986E41\ \(Prime\ Time\ Wrestling\).mp4 -to 00:02:04 0.mp4 -ss 00:13:56  -to 00:15:28 1.mp4 -ss 00:21:40  -to 00:22:24 2.mp4 -ss 00:27:31  -to 00:28:33 3.mp4 -ss 00:30:40  -to 00:31:12 4.mp4 -ss 00:37:10  -to 00:39:08 5.mp4 -ss 00:44:39  -to 00:45:22 6.mp4 -ss 00:50:30  -to 00:51:37 7.mp4 -ss 00:53:45 8.mp4 && printf "file '0.mp4'\nfile '1.mp4'\nfile '2.mp4'\nfile '3.mp4'\nfile '4.mp4'\nfile '5.mp4'\nfile '6.mp4'\nfile '7.mp4'\nfile '8.mp4'" > concat.txt && ffmpeg -f concat -safe 0 -i concat.txt -c copy 1986.10.21.mp4 && rm {0,1,2,3,4,5,6,7,8}.mp4 && rm concat.txt && say all done
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
