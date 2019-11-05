# WWE Network Download

This is a proof of concept to understand how to download videos from a video streaming platform.

The code was originally written by [@freyta](https://github.com/freyta/) and I was granted permission to refactor his code and to host it here.

> Note: I do not endorse piracy. This is for educational purposes only. I hold no responsibility.

## Requirements

- Python3: `brew install python3`
- FFMPEG: `brew install ffmpeg`

### Optional

This command-line application offers a `-s, --speak` flag which uses a 'Text-to-Speech' program. You don't have to use this flag to run the command-line application and so the required speech program is not _required_.

By default we use the `say` command which is available by default on macOS. If you're on Linux then you could modify this code to utilize something like `espeak` instead.

## Usage

```
usage: main.py [-h] [-u USER] [-p PASSWORD] [-l LINK] [-f FILES]

Download videos from the WWE Network

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  WWE Network user account.
  -p PASSWORD, --password PASSWORD
                        WWE Network account password.
  -l LINK, --link LINK  Video link to download.
  -f FILES, --files FILES
                        File with list of links
  -d DEBUG, --debug DEBUG
                        Dry-run displays ffmpeg commands.
  -v VERBOSE, --verbose VERBOSE
                        Verbose prints ffmpeg output.
  -i INDEX, --index INDEX
                        Index adds indices to filenames.
  -s SPEAK, --speak SPEAK
                        Use `say` binary for alerts.
  -o OUTPUT, --output OUTPUT
                        Directory to place files into.
```

## Examples

- [Login credentials provided by environment variables](#login-credentials-provided-by-environment-variables)
- [Login credentials provided by CLI flags](#login-credentials-provided-by-CLI-flags)
- [Multiple videos downloaded in parallel](#multiple-videos-downloaded-in-parallel)
- [Change output directory](#change-output-directory)
- [Insert numeric index in filenames](#insert-numeric-index-in-filenames)
- [Debug Mode](#debug-mode)
- [Verbose Mode](#verbose-mode)
- [Speak Mode](#speak-mode)

### Login credentials provided by environment variables:

```bash
export WWE_USER=foo WWE_PASS=bar && python3 main.py -l <url>
```

In the above example, `<url>` is either:

- `https://watch.wwe.com/episode/Prime-Time-Wrestling-9702`
- `/episode/Prime-Time-Wrestling-9702`
- `episode/Prime-Time-Wrestling-9702`

### Login credentials provided by CLI flags

```bash
python3 main.py -u foo -p bar -l <url> 
```

### Multiple videos downloaded in parallel

```bash
python3 main.py -u foo -p bar -f files.txt
```

In the above example, `files.txt` is a file consisting of multiple video URLs (one per line).

> Note: we use a process 'pool' to prevent creating more subprocesses than we have cores.

### Change output directory

If you wish to not have the files downloaded to the same directory as where you are running the CLI command from, then use the `-o, --output` flag to inform the binary of where to download the files to.

```bash
python3 main.py -u foo -p bar -f files.txt -o /Volumes/MyExternalDrive/...
```

### Insert numeric index in filenames

If you're using the `-f, --files` flag to download multiple videos at once, then those videos could be part of a show (e.g. The Monday Night Wars) where the episodes are in a sequential order.

If you include the `-i, --index` flag with your command, then we'll presume the order in the `-f, --files` file will be in order, and we'll simply insert a numerical index to the output filename.

For example, if you provided `--files videos.txt` and your `videos.txt` contained the following...

```
https://watch.wwe.com/episode/The-War-Begins-9762
https://watch.wwe.com/episode/The-Rise-of-the-nWo-9779
https://watch.wwe.com/episode/Embracing-a-New-Attitude-9078
```

Then we would download the videos and output the filenames as:

```
1. The_War_Begins.mp4
2. The_Rise_of_the_nwo.mp4
3. Embracing_a_New_Attitude.mp4
```

### Debug Mode

Debug mode will print the `ffmpeg` command that the application generates for accessing a specified video.

No downloading of the stream URL will occur.

```bash
python3 main.py -u foo -p bar -f files.txt -d true
```

> Note: omit the `-d, --debug` flag if you don't require debug mode.

### Verbose Mode

Verbose mode will print the output from the generated `ffmpeg` command which streams the provided video(s).

```bash
python3 main.py -u foo -p bar -f files.txt -v true
```

> Note: omit the `-v, --verbose` flag if you don't require verbose mode.

### Speak Mode

Speak mode will use the `say` command (available by default on macOS) to notify you of important things happening. 

For example, rather than having to keep an eye on your terminal to see when a new batch of subprocesses is opened (e.g. when providing a list of videos using the `-f, --files` flag), you can now use the `-s, --speak` flag and the terminal will speak out loud that this is happening.

```bash
python3 main.py -u foo -p bar -f files.txt -s true
```

## TODO

Add stdout printing of the download file size so people can see how the progress is going.

A temporary solution is to `brew install watch` and to run:

```bash
watch -n 1 ls -lah '*.mp4'
```
