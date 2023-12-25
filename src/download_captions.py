#!/usr/bin/env python3
import os
import json
import html
from downloader import Downloader

def main():

  # init
  downloader = Downloader()
  if not os.path.exists('captions'):
    os.mkdir('captions')

  videos = json.load(open('videos.json'))
  for video in videos:

    # clean
    video['snippet']['title'] = html.unescape(video['snippet']['title'])

    # get info
    id = video['id']['videoId']
    title = video['snippet']['title']

    # do not process if already downloaded
    if os.path.exists(f'captions/{id}.original.vtt'):
      original = open(f'captions/{id}.original.vtt', 'r').read()
    else:
      print(f'[youtube] downloading captions for {id}: {title}...')
      original = downloader.download_captions(id)
      with open(f'captions/{id}.original.vtt', 'w') as f:
        f.write(original)

    # prepare captions
    print(f'[youtube] preparing captions for {id}: {title}...')
    prepared = downloader.prepare_captions(video, original)
    with open(f'captions/{id}.cleaned.vtt', 'w') as f:
      f.write(prepared)

if __name__ == '__main__':
  main()
