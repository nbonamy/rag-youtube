#!/usr/bin/env python3
import os
import json
import consts
import utils
from config import Config
from agent_load import Loader
from langchain_community.document_loaders import DirectoryLoader, TextLoader

def main():

  # init
  config = Config(consts.CONFIG_PATH)
  loader = Loader(config)

  # loader = DirectoryLoader('./captions', glob="./_*.cleaned.vtt", loader_cls=TextLoader)
  # documents = loader.load()
  # loader.add_documents(documents, {})
  # return

  # print config
  print(f'[loader] embeddings model = {config.embeddings_model()}')
  print(f'[loader] splitter size/overlap = {config.split_chunk_size()}/{config.split_chunk_overlap()}')
  utils.dumpj({
    'embeddings_model': config.embeddings_model(),
    'split_chunk_size': config.split_chunk_size(),
    'split_chunk_overlap': config.split_chunk_overlap(),
  }, 'db_config.json')

  # track loaded
  loaded = []
  if os.path.exists(config.db_persist_directory()) and os.path.exists('loaded.json'):
    loaded = json.load(open('loaded.json'))

  # iterate on captions files
  subset_only=False
  all_files = [f for f in os.listdir('captions') if 'cleaned' in f and f not in loaded and (not subset_only or f.startswith('_'))]
  all_files.sort()

  # load
  index = 0
  for filename in all_files:
    
    # init
    index += 1
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
      print(f'[loader][{index}/{len(all_files)}] adding {video_id} to database...')
      with open(f'captions/{filename}') as f:
        loader.add_text(f.read(), metadata)
    
      # update index
      loaded.append(filename)
      json.dump(loaded, open('loaded.json', 'w'), indent=2)
    
    except Exception as e:
      print(f'[loader] error adding {video_id} to database: {e}')
      continue

if __name__ == '__main__':
  main()
