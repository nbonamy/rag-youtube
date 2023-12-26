#!/usr/bin/env python3
import os
import json
import consts
import utils
from agent import Agent
from config import Config
from langchain.document_loaders import DirectoryLoader, TextLoader

def main():

  # init
  config = Config(consts.CONFIG_PATH)
  agent = Agent(config)

  # loader = DirectoryLoader('./captions', glob="./_*.cleaned.vtt", loader_cls=TextLoader)
  # documents = loader.load()
  # agent.add_documents(documents, {})
  # return

  # track loaded
  loaded = []
  if os.path.exists(config.persist_directory()) and os.path.exists('loaded.json'):
    loaded = json.load(open('loaded.json'))

  # iterate on captions files
  text = ''
  for filename in os.listdir('captions'):

    # skip original files
    if 'original' in filename:
      continue

    # skip if already loaded
    if filename in loaded:
      continue

    # # debug
    # if not filename.startswith('_'):
    #   continue

    # get sone metadata
    video_id = filename.split('.')[0]

    # find title
    metadata = {
      'title': 'Unknown',
      'description': 'Unknown',
      'url': utils.get_video_url(video_id),
      'source': video_id,
    }
    video = utils.get_video_info(video_id)
    if video is not None:
      metadata['title'] = video['snippet']['title']
      metadata['description'] = video['snippet']['description']

    # load
    try:
    
      # do it
      print(f'[loader] adding {filename} to database...')
      with open(f'captions/{filename}') as f:
        agent.add_text(f.read(), metadata)
    
      # update index
      loaded.append(filename)
      json.dump(loaded, open('loaded.json', 'w'), indent=2)
    
    except Exception as e:
      print(f'[loader] error adding {filename} to database: {e}')
      continue

if __name__ == '__main__':
  main()
