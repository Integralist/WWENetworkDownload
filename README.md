# WWE Network Download

This is a proof of concept to understand how to download videos from a video streaming platform.

The code was originally written by [@freyta](https://github.com/freyta/) and I was granted permission to refactor his code and to host it here.

> Note: I do not endorse piracy. This is for educational purposes only. I hold no responsibility.

## Requirements

- Python3: `brew install python3`
- FFMPEG: `brew install ffmpeg`

## Usage

```
usage: main.py [-h] [-u USER] [-p PASSWORD] [-l LINK] [-f FILES] [-d DEBUG]

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
                        Dry-run.
```

## Examples

- [Login credentials provided by environment variables](#login-credentials-provided-by-environment-variables)
- [Login credentials provided by CLI flags](#login-credentials-provided-by-CLI-flags)
- [Multiple videos downloaded in parallel](#multiple-videos-downloaded-in-parallel)
- [Debug Mode](#debug-mode)

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
python3 main.py -u foo -p bar -l <url> -f files.txt
```

In the above example, `files.txt` is a file consisting of multiple video URLs (one per line).

> Note: we use a process 'pool' to prevent creating more subprocesses than we have cores.

### Debug Mode

To see a dry-run of the `ffmpeg` command that will be produced, pass the 'debug' flag:

```bash
python3 main.py -u foo -p bar -l /episode/The-War-Begins-9762 -d true
```

> Note: for details of the various CLI flags use `--help` or `-h`.
