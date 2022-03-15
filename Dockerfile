FROM python:slim

WORKDIR /stefan
COPY . .

RUN python3 -m pip install -r requirements.txt

RUN apt -y update
RUN apt -y upgrade
RUN apt -y install ffmpeg

CMD python3 main.py