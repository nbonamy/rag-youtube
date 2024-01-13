
import utils
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler

class CallbackHandler(BaseCallbackHandler):
  def __init__(self, parameters):
    super().__init__()
    self.reset()
    self.parameters = parameters

  def __getitem__(self, x):
    return getattr(self, x)

  def reset(self):
    self.id = None
    self.runs = []
    self.outputs = None
    self.start = None
    self.end = None
  
  def set_sources(self, sources: list) -> None:
    self.sources = sources

  def on_chain_start(self, serialized: dict, inputs: dict, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    if parent_run_id is None:
      self.id = run_id.hex
      self.start = utils.now()
    else:
      parent = self.__get_run(parent_run_id)
      parent['runs'].append({
        'id': run_id.hex,
        'type': 'chain',
        'repr': self.__get_repr(serialized),
        'start': utils.now(),
        'end': None,
        'elapsed': None,
        'runs': [],
      })

  def on_chain_end(self, outputs: dict, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    if run_id.hex == self.id:
      self.outputs = outputs
      self.end = utils.now()
    else:
      run = self.__get_run(run_id)
      if run is None:
        print(f'[agent] on_chain_end called for unknown run id {run_id}')
        return
      run['end'] = utils.now()
      run['elapsed'] = run['end'] - run['start']

  def on_llm_start(self, serialized: dict, prompts: list, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[agent] llm starting ("{prompts[0][0:64]}...")')
    parent = self.__get_run(parent_run_id)
    parent['runs'].append({
      'id': run_id.hex,
      'type': 'llm',
      'repr': self.__get_repr(serialized),
      'prompt': prompts[0],
      'response': None,
      'tokens': 0,
      'created': utils.now(),
      'start': None,
      'end': None,
      'elapsed': None,
      'time_1st_token': None,
      'tokens_per_sec': None,
      'runs': [],
    })

  def on_llm_new_token(self, token: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    run = self.__get_run(run_id)
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
    run = self.__get_run(run_id)
    if run is None:
      print(f'[agent] on_llm_end called for unknown run id {run_id}')
      return
    run['end'] = utils.now()
    run['elapsed'] = run['end'] - run['start']
    run['time_1st_token'] = self.__time_1st_token(run)
    run['tokens_per_sec'] = self.__tokens_per_sec(run)
  
  def on_retriever_start(self, serialized: dict, query: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[agent] retriever starting ("{query[0:64]}...")')
    parent = self.__get_run(parent_run_id)
    parent['runs'].append({
      'id': run_id.hex,
      'type': 'retriever',
      'repr': self.__get_repr(serialized),
      'query': query,
      'documents': None,
      'created': utils.now(),
      'start': utils.now(),
      'end': None,
      'elapsed': None,
      'runs': [],
    })

  def on_retriever_end(self, documents: any, run_id: UUID, **kwargs) -> None:
    run = self.__get_run(run_id)
    if run is None:
      print(f'[agent] on_retriever_end called for unknown run id {run_id}')
      return
    print(f'[agent] retrieved {len(documents)} relevant documents')
    run['documents'] = [doc.metadata['source'] for doc in documents]
    run['end'] = utils.now()
    run['elapsed'] = run['end'] - run['start']

  def output(self) -> dict:
    return {
      'text': self.outputs['result'].strip() if 'result' in self.outputs else '',
      'sources': self.sources,
      'runs': self.runs,
      'parameters': self.parameters.to_dict(),
      'performance': {
        'total_time': int(self.end - self.start),
        'tokens': self.__get_sum_across_llm_runs('tokens'),
        'time_1st_token': self.__get_avg_across_llm_runs('time_1st_token'),
        'tokens_per_sec': self.__get_avg_across_llm_runs('tokens_per_sec'),
      }
    }

  def __time_1st_token(self, run) -> int:
    return None if run['start'] is None else int(run['start'] - run['created'])

  def __tokens_per_sec(self, run)  -> float:
    return None if run['start'] is None else round(run['tokens'] / (run['end'] - run['start']) * 1000, 2)

  def __get_sum_across_llm_runs(self, key: str) -> any:
    return sum(value for value in self.__get_not_none_across_llm_runs(key))

  def __get_avg_across_llm_runs(self, key: str) -> any:
    values = self.__get_not_none_across_llm_runs(key)
    return round(sum(value for value in values) / len(values), 2)

  def __get_not_none_across_llm_runs(self, key: str) -> list:
    return [run[key] for run in self.__get_llm_runs() if run[key] is not None]

  def __get_run(self, id: UUID, runs=None) -> dict:
    if id is None or self.id == id.hex:
      return self
    if runs is None:
      runs = self.runs
    for run in runs:
      if run['id'] == id.hex:
        return run
      sub_run = self.__get_run(id=id, runs=run['runs'])
      if sub_run is not None:
        return sub_run
    return None

  def __get_llm_runs(self, runs=None) -> list:
    llm_runs = []
    if runs is None:
      runs = self.runs
    for run in runs:
      if run['type'] == 'llm':
        llm_runs.append(run)
      llm_runs.extend(self.__get_llm_runs(run['runs']))
    return llm_runs

  def __get_repr(self, serialized: dict) -> str:
    if 'repr' in serialized:
      return serialized['repr']
    if 'kwargs' in serialized:
      for kwarg  in serialized['kwargs']:
        repr = self.__get_repr(serialized['kwargs'][kwarg])
        if repr is not None:
          return None
    return None