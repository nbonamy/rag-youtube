import configparser

# config
CONFIG_SECTION_GENERAL = 'General'

class Config:

  config = None

  def __init__(self, path):
    self.config = configparser.ConfigParser()
    self.config.read(path)

  def ollama_url(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_url') or 'http://localhost:11434'
  
  def ollama_model(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'ollama_model') or 'mistral:latest'
  
  def persist_directory(self):
    return self.__get_value(CONFIG_SECTION_GENERAL, 'persist_dir') or 'db'


  def __get_value(self, section, option):
    if self.config.has_option(section, option):
      return self.config.get(section, option).strip("'")
    else:
      return None
