#!/usr/bin/env python3
import os
import sys
import json
import html
from downloader import Downloader

def main():

  # init
  downloader = Downloader()
  if not os.path.exists('captions'):
    os.mkdir('captions')

  # lang
  lang = None if len(sys.argv) == 1 else sys.argv[1]

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
      original = downloader.download_captions(id, lang)
      if original is None:
        continue
      with open(f'captions/{id}.original.vtt', 'w') as f:
        f.write(original)

    # prepare captions
    print(f'[youtube] preparing captions for {id}: {title}...')
    prepared = downloader.prepare_captions(video, original)
    with open(f'captions/{id}.cleaned.vtt', 'w') as f:
      f.write(prepared)

if __name__ == '__main__':
  main()
