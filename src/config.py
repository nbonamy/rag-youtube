
import consts
import configparser

# config
CONFIG_SECTION_GENERAL = 'General'
CONFIG_SECTION_EMBEDDINGS = 'Embeddings'
CONFIG_SECTION_SPLITTER = 'Splitter'
CONFIG_SECTION_SEARCH = 'Search'

class Config:

  config = None

  def __init__(self, path):
    self.config = configparser.ConfigParser()
    self.config.read(path)

  def ollama_url(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_url') or consts.DEFAULT_OLLAMA_URL
  
  # https://ollama.ai/library
  def ollama_model(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_model') or consts.DEFAULT_OLLAMA_MODEL

  def persist_directory(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'persist_dir') or consts.DEFAULT_PERSIST_DIR

  def conversational_chain(self):
    value = self.__get_value(CONFIG_SECTION_GENERAL, 'conversational') or consts.DEFAULT_CONVERSATIONAL
    return self.__is_bool(value)

  def embeddings_model(self):
    return self.__get_value(CONFIG_SECTION_EMBEDDINGS, 'model') or consts.DEFAULT_EMBEDDINGS_MODEL

  def split_chunk_size(self):
    return int(self.__get_value(CONFIG_SECTION_SPLITTER, 'split_chunk_size') or consts.DEFAULT_SPLIT_CHUNK_SIZE)

  def split_chunk_overlap(self):
    return int(self.__get_value(CONFIG_SECTION_SPLITTER, 'split_chunk_overlap') or consts.DEFAULT_SPLIT_CHUNK_OVERLAP)

  def similarity_document_count(self):
    return int(self.__get_value(CONFIG_SECTION_SEARCH, 'similarity_document_count') or consts.DEFAULT_SIMILARITY_DOCUMENT_COUNT)

  def __get_value(self, section, option):
    if self.config.has_option(section, option):
      return self.config.get(section, option).strip("'")
    else:
      return None

  def __is_bool(self, value):
    return value.lower() in ['true', '1', 'y', 'yes', 'on' ]
