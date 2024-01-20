#!/usr/bin/env python3
from agent_base import AgentBase
from callback import CallbackHandler
from chain_base import ChainParameters
from chain_eval_qa import QAEvalChain
from chain_eval_criteria import CriteriaEvalChain
from langchain_community.llms import Ollama

class Evaluator(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_database()

  def evaluate_criteria(self, run_id: str, answer: str, criteria: list, overrides: dict) -> dict:

    # fetch answer
    if answer is None or len(answer) == 0:
      run = self.database.get_run(run_id)
      if run is None:
        raise Exception(f'run {run_id} not found')
      answer = run['trace']['answer']
    
    # log
    print(f'[eval] evaluating {answer[0:64]} against {", ".join(criteria)}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    llm = self._build_llm(parameters)
    chain = CriteriaEvalChain(llm, criteria, callback_handler, parameters)

    # now query
    chain.invoke(answer)

    # done
    res = callback_handler.to_dict()

    # process answer
    res['evaluation'] = {}
    answer = res['answer']
    ratings = answer.split('\n')
    for rating in ratings:
      try:
        tokens = rating.split(':')
        if len(tokens) == 2:
          criteria_name = tokens[0].strip()
          rating_value = int(tokens[1].split('(')[0])
          res['evaluation'][criteria_name] = rating_value
      except:
        pass

    # make sure we have all criteria
    if len(criteria) != len(res['evaluation'].keys()):
      res['evaluation'] = {}

    # save it
    try:
      self.database.set_run_eval_crit(run_id, res)
    except Exception as e:
      print(f'[agent] failed to update run: {e}')
      pass
    
    # done
    return res
  
  def evaluate_qa(self, run_id: str, question: str, answer: str, reference: str, overrides: dict) -> dict:

    # fetch run
    if question is None or len(question) == 0 or answer is None or len(answer) == 0:
      run = self.database.get_run(run_id)
      if run is None:
        raise Exception(f'run {run_id} not found')
      question = run['trace']['question']
      answer = run['trace']['answer']
    
    # log
    print(f'[eval] evaluating {answer[0:64]}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    llm = self._build_llm(parameters)
    chain = QAEvalChain(llm, callback_handler)

    # now query
    chain.invoke(question, answer, reference)

    # done
    res = callback_handler.to_dict()

    # save it
    try:
      self.database.set_run_eval_qa(run_id, res)
    except Exception as e:
      print(f'[agent] failed to update run: {e}')
      pass
    
    # done
    return res

  def _build_llm(self, parameters: ChainParameters) -> Ollama:
    parameters.llm_temperature = 0.0
    return super()._build_llm(parameters)
