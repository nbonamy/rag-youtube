
import utils
from langchain.callbacks.base import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
  def __init__(self):
    self.reset()

  def reset(self):
    self.created = utils.now()
    self.text = None
    self.sources = []
    self.start = None
    self.end = None
    self.tokens = 0

  def set_sources(self, sources: list) -> None:
    self.sources = sources

  def on_llm_start(self, serialized: dict, prompts: dict, **kwargs) -> None:
    print('[database] llm starting')
    self.reset()
  
  def on_llm_new_token(self, token: str, **kwargs) -> None:
    if self.text is None:
      self.text = token
      self.start = utils.now()
      self.end = utils.now()
      self.tokens = 1
    else:
      self.text += token
      self.tokens += 1
      self.end = utils.now()

  def time_1st_token(self) -> float:
    return self.start - self.created

  def tokens_per_sec(self)  -> float:
    return self.tokens / (self.end - self.start) * 1000

  def output(self) -> dict:
    return {
      'text': self.text.strip(),
      'sources': self.sources,
      'performance': {
        'tokens': self.tokens,
        'time_1st_token': int(self.time_1st_token()),
        'tokens_per_sec': round(self.tokens_per_sec(), 2)
      }
    }