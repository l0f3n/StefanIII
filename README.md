# Stefan III 

## Local

### Installation

```
python3 -m pip install virtualenv
python3 -m venv venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

### Usage

```
python3 src/main.py
```

## Docker

### Installation

```
docker build -t stefan .
```

### Usage

Set the environment variables `DISCORD_TOKEN`, `SPOTIFY_ID` and `SPOTIFY_SECRET` to the appropriate values.

```
docker run -e DISCORD_TOKEN -e SPOTIFY_ID -e SPOTIFY_SECRET stefan
```
