
import utils
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

  def debug(self):
    value = self.__get_value(CONFIG_SECTION_GENERAL, 'debug') or consts.DEFAULT_DEBUG
    return utils.is_true(value)

  def database_path(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'database_path') or consts.DEFAULT_DATABASE_PATH

  def ollama_url(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_url') or consts.DEFAULT_OLLAMA_URL
  
  # https://ollama.ai/library
  def ollama_model(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_model') or consts.DEFAULT_OLLAMA_MODEL
  
  def llm_temperature(self):
    return float(self.__get_value(CONFIG_SECTION_GENERAL, 'llm_temperature') or consts.DEFAULT_LLM_TEMPERATURE)

  def db_persist_directory(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'db_persist_dir') or consts.DEFAULT_DB_PERSIST_DIR

  def embeddings_model(self):
    return self.__get_value(CONFIG_SECTION_EMBEDDINGS, 'model') or consts.DEFAULT_EMBEDDINGS_MODEL

  def split_chunk_size(self):
    return int(self.__get_value(CONFIG_SECTION_SPLITTER, 'split_chunk_size') or consts.DEFAULT_SPLIT_CHUNK_SIZE)

  def split_chunk_overlap(self):
    return int(self.__get_value(CONFIG_SECTION_SPLITTER, 'split_chunk_overlap') or consts.DEFAULT_SPLIT_CHUNK_OVERLAP)

  # base, sources, conversation
  def chain_type(self):
    return self.__get_value(CONFIG_SECTION_SEARCH, 'chain_type') or consts.DEFAULT_CHAIN_TYPE

  def doc_chain_type(self):
    return self.__get_value(CONFIG_SECTION_SEARCH, 'doc_chain_type') or consts.DEFAULT_DOC_CHAIN_TYPE

  def retriever_type(self):
    return self.__get_value(CONFIG_SECTION_SEARCH, 'retriever_type') or consts.DEFAULT_RETRIEVER_TYPE
  
  def search_type(self):
    return self.__get_value(CONFIG_SECTION_SEARCH, 'search_type') or consts.DEFAULT_SEARCH_TYPE
  
  def memory_type(self):
    return self.__get_value(CONFIG_SECTION_SEARCH, 'memory_type') or consts.DEFAULT_MEMORY_TYPE

  def document_count(self):
    return int(self.__get_value(CONFIG_SECTION_SEARCH, 'document_count') or consts.DEFAULT_DOCUMENT_COUNT)

  def score_threshold(self):
    return float(self.__get_value(CONFIG_SECTION_SEARCH, 'score_threshold') or consts.DEFAULT_SCORE_THRESHOLD)

  def custom_prompts(self):
    value = self.__get_value(CONFIG_SECTION_SEARCH, 'custom_prompts') or consts.DEFAULT_CUSTOM_PROMPTS
    return utils.is_true(value)

  def return_sources(self):
    value = self.__get_value(CONFIG_SECTION_SEARCH, 'return_sources') or consts.DEFAULT_RETURN_SOURCES
    return utils.is_true(value)

  def __get_value(self, section, option):
    if self.config.has_option(section, option):
      return self.config.get(section, option).strip("'")
    else:
      return None
