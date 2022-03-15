# Installation

## Locally

```
python3 -m pip install virtualenv
python3 -m venv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

## Docker

Set the environment variables `DISCORD_TOKEN`, `SPOTIFY_ID` and `SPOTIFY_SECRET` to the appropriate values.

```
docker build -t stefan .
docker run -e DISCORD_TOKEN -e SPOTIFY_ID -e SPOTIFY_SECRET stefan
```