
import utils
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler

class CallbackHandler(BaseCallbackHandler):
  def __init__(self, parameters):
    super().__init__()
    self.reset()
    self.parameters = parameters

  def reset(self):
    self.llm_runs = []
    self.retriever_runs = []
    self.start = None
    self.end = None
    self.last_run_id = None
  
  def set_sources(self, sources: list) -> None:
    self.sources = sources

  def on_llm_start(self, serialized: dict, prompts: list, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[agent] llm starting ("{prompts[0][0:64]}...")')
    if self.start is None:
      self.start = utils.now()
    self.llm_runs.append({
      'id': run_id.hex,
      'parent_id': parent_run_id.hex,
      'prompt': prompts[0],
      'response': None,
      'tokens': 0,
      'created': utils.now(),
      'start': None,
      'end': None,
      'time_1st_token': None,
      'tokens_per_sec': None
    })

  def on_llm_new_token(self, token: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    run = self.__get_llm_run(run_id)
    if run is None:
      print(f'[agent] on_llm_new_token called for unknown run id {run_id}')
      return
    if run['response'] is None:
      run['start'] = utils.now()
      run['response'] = ''
      run['tokens'] = 0
    run['response'] += token
    run['tokens'] += 1
    run['end'] = utils.now()

  def on_llm_end(self, response: dict, run_id: UUID, **kwargs) -> None:
    self.end = utils.now()
    self.last_run_id = run_id
    run = self.__get_llm_run(run_id)
    if run is None:
      print(f'[agent] on_llm_end called for unknown run id {run_id}')
      return
    run['end'] = utils.now()
    run['time_1st_token'] = self.__time_1st_token(run)
    run['tokens_per_sec'] = self.__tokens_per_sec(run)
  
  def on_retriever_start(self, serialized: dict, query: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[agent] retriever starting ("{query[0:64]}...")')
    self.retriever_runs.append({
      'id': run_id.hex,
      'parent_id': parent_run_id.hex,
      'query': query,
      'documents': None,
      'created': utils.now(),
      'start': utils.now(),
      'end': None,
    })

  def on_retriever_end(self, documents: any, run_id: UUID, **kwargs) -> None:
    run = self.__get_retriever_run(run_id)
    if run is None:
      print(f'[agent] on_retriever_end called for unknown run id {run_id}')
      return
    #run.documents = documents
    run['end'] = utils.now()
    run['duration'] = run['end'] - run['start']

  def output(self) -> dict:
    last_run = self.__get_llm_run(self.last_run_id)
    return {
      'text': '' if last_run['response'] is None else last_run['response'].strip(),
      'sources': self.sources,
      'llm_runs': self.llm_runs,
      'retreiver_runs': self.retriever_runs,
      'parameters': self.parameters.to_dict(),
      'performance': {
        'total_time': int(self.end - self.start),
        'tokens': self.__get_sum_across_runs('tokens'),
        'time_1st_token': self.__get_avg_across_runs('time_1st_token'),
        'tokens_per_sec': self.__get_avg_across_runs('tokens_per_sec'),
      }
    }

  def __time_1st_token(self, run) -> int:
    return None if run['start'] is None else int(run['start'] - run['created'])

  def __tokens_per_sec(self, run)  -> float:
    return None if run['start'] is None else round(run['tokens'] / (run['end'] - run['start']) * 1000, 2)

  def __get_sum_across_runs(self, key: str) -> any:
    return sum(value for value in self.__get_not_none_across_runs(key))

  def __get_avg_across_runs(self, key: str) -> any:
    values = self.__get_not_none_across_runs(key)
    return round(sum(value for value in values) / len(values), 2)

  def __get_not_none_across_runs(self, key: str) -> list:
    return [run[key] for run in self.llm_runs if run[key] is not None]

  def __get_llm_run(self, id: UUID) -> dict:
    for run in self.llm_runs:
      if run['id'] == id.hex:
        return run
    return None

  def __get_retriever_run(self, id: UUID) -> dict:
    for run in self.retriever_runs:
      if run['id'] == id.hex:
        return run
    return None