
import re
import utils
import tiktoken
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler

class ChainStep:

  def __init__(self, id: UUID, type: str, serialized: dict, auto_start:bool=True, **kwargs):
    self.id = id
    self.type = type
    self.repr = self.__get_repr(serialized)
    self.args = kwargs or {}
    self.created_at = utils.now()
    self.started_at = self.created_at if auto_start else None
    self.ended_at = None
    self.elapsed = None
    self.steps = []

  def start(self):
    self.started_at = utils.now()

  def end(self):
    self.ended_at = utils.now()
    self.elapsed = self.ended_at - self.created_at

  def add_step(self, step):
    self.steps.append(step)

  def to_dict(self):
    return {
      'id': self.id.hex,
      'type': self.type,
      'repr': self.repr,
      'created_at': self.created_at,
      'started_at': self.started_at,
      'ended_at': self.ended_at,
      'elapsed': self.elapsed,
      'steps': [step.to_dict() for step in self.steps],
    } | self.args

  def __getitem__(self, x):
    return self.args[x] if x in self.args else None
  
  def __setitem__(self, x, value):
    self.args[x] = value

  def __get_repr(self, serialized: dict) -> str:
    repr = self.__find_attr(serialized, 'repr')
    return None if repr is None else re.sub(r'PromptTemplate\(.*?[^\\]\'\)', 'PromptTemplate(…)', repr)

  def __find_attr(self, serialized: dict, key: str) -> str:
    if key in serialized:
      return serialized[key]
    if 'kwargs' in serialized:
      for kwarg in serialized['kwargs']:
        if kwarg == key:
          return serialized['kwargs'][key]
        value = self.__find_attr(serialized['kwargs'][kwarg], key)
        if value is not None:
          return value
    return None

class CallbackHandler(BaseCallbackHandler):
  def __init__(self, question, parameters):
    super().__init__()
    self.reset()
    self.question = question
    self.parameters = parameters

  def reset(self):
    self.root = None
    self.outputs = None
    self.sources = None
  
  def set_sources(self, sources: list) -> None:
    self.sources = sources

  def on_chain_start(self, serialized: dict, inputs: dict, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    if parent_run_id is None:
      self.root = ChainStep(run_id, 'chain', serialized)
    else:
      parent = self.__get_step(parent_run_id)
      parent.add_step(ChainStep(run_id, 'chain', serialized))

  def on_chain_end(self, outputs: dict, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    if run_id == self.root.id:
      self.outputs = outputs
      self.root.end()
    else:
      run = self.__get_step(run_id)
      if run is None:
        print(f'[chain] on_chain_end called for unknown run id {run_id}')
        return
      run.end()

  def on_llm_start(self, serialized: dict, prompts: list, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[chain] llm starting ("{prompts[0][0:64]}...")')
    parent = self.__get_step(parent_run_id)
    parent.add_step(ChainStep(
      run_id, 'llm', serialized, auto_start=False,
      prompt=prompts[0], input_tokens=self.__count_tokens(prompts[0]),
      response=None, output_tokens=0,
      time_1st_token=None, tokens_per_sec=None
    ))

  def on_llm_new_token(self, token: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    run = self.__get_step(run_id)
    if run is None:
      print(f'[chain] on_llm_new_token called for unknown run id {run_id}')
      return
    if run['response'] is None:
      run.start()
      run['response'] = ''
    run['response'] += token
    run['output_tokens'] += 1

  def on_llm_end(self, response: dict, run_id: UUID, **kwargs) -> None:
    run = self.__get_step(run_id)
    if run is None:
      print(f'[chain] on_llm_end called for unknown run id {run_id}')
      return
    run.end()
    run['time_1st_token'] = self.__time_1st_token(run)
    run['tokens_per_sec'] = self.__tokens_per_sec(run)
  
  def on_retriever_start(self, serialized: dict, query: str, run_id: UUID, parent_run_id: UUID, **kwargs) -> None:
    print(f'[chain] retriever starting ("{query[0:64]}...")')
    parent = self.__get_step(parent_run_id)
    parent.add_step(ChainStep(
      run_id, 'retriever', serialized,
      query=query, documents=None
    ))

  def on_retriever_end(self, documents: any, run_id: UUID, **kwargs) -> None:
    run = self.__get_step(run_id)
    if run is None:
      print(f'[chain] on_retriever_end called for unknown run id {run_id}')
      return
    print(f'[chain] retrieved {len(documents)} relevant documents')
    run.end()
    run['documents'] = [doc.metadata for doc in documents]

  def to_dict(self) -> dict:
    res={
      'question': self.question,
      'answer': self.__final_answer(),
      'sources': self.sources,
      'chain': self.root.to_dict(),
      'parameters': self.parameters.to_dict(),
      'performance': {
        'total_time': int(self.root.ended_at - self.root.created_at),
        'input_tokens': self.__get_sum_across_llm_runs('input_tokens'),
        'output_tokens': self.__get_sum_across_llm_runs('output_tokens'),
        'time_1st_token': self.__get_avg_across_llm_runs('time_1st_token'),
        'tokens_per_sec': self.__get_avg_across_llm_runs('tokens_per_sec'),
      }
    }
    res['performance']['cost'] = utils.cost(res['performance']['input_tokens'], res['performance']['output_tokens'])
    return res

  def __final_answer(self):
    if self.outputs is None:
      return ''
    if len(self.outputs.keys()) == 1:
      return self.outputs[list(self.outputs.keys())[0]].strip()
    if 'result' in self.outputs:
      return self.outputs['result'].strip()
    if 'answer' in self.outputs:
      return self.outputs['answer'].strip()
    if 'text' in self.outputs:
      return self.outputs['text'].strip()
    return ''
  
  def __time_1st_token(self, run) -> int:
    return None if run.started_at is None else int(run.started_at - run.created_at)

  def __tokens_per_sec(self, run)  -> float:
    return None if run.started_at is None else round(run['output_tokens'] / (run.ended_at - run.started_at) * 1000, 2)

  def __get_sum_across_llm_runs(self, key: str) -> any:
    return sum(value for value in self.__get_not_none_across_llm_runs(key))

  def __get_avg_across_llm_runs(self, key: str) -> any:
    values = self.__get_not_none_across_llm_runs(key)
    return round(sum(value for value in values) / len(values), 2)

  def __get_not_none_across_llm_runs(self, key: str) -> list:
    return [run[key] for run in self.__get_llm_runs() if run[key] is not None]

  def __get_step(self, id: UUID, runs=None) -> dict:
    if id is None or self.root.id == id:
      return self.root
    if runs is None:
      runs = self.root.steps
    for run in runs:
      if run.id == id:
        return run
      sub_run = self.__get_step(id=id, runs=run.steps)
      if sub_run is not None:
        return sub_run
    return None

  def __get_llm_runs(self, runs=None) -> list:
    llm_runs = []
    if runs is None:
      runs = self.root.steps
    for run in runs:
      if run.type == 'llm':
        llm_runs.append(run)
      llm_runs.extend(self.__get_llm_runs(run.steps))
    return llm_runs

  def __count_tokens(self, text: str) -> int:
    enc = tiktoken.encoding_for_model('gpt-4')
    return len(enc.encode(text))