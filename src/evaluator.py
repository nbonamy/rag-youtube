#!/usr/bin/env python3
import langchain
from langchain_community.llms import Ollama
from chain_base import ChainParameters
from chain_eval_qa import QAEvalChain
from chain_eval_criteria import CriteriaEvalChain
from callback import CallbackHandler

class Evaluator:

  def __init__(self, config):
    if config.debug():
      langchain.verbose = True
      langchain.debug = True
    self.config = config
  
  def evaluate_criteria(self, answer: str, criteria: list, overrides: dict) -> dict:

    # log
    print(f'[eval] evaluating {answer[0:64]} against {", ".join(criteria)}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    ollama = Ollama(base_url=self.config.ollama_url(), model=parameters.ollama_model)
    chain = CriteriaEvalChain(ollama, criteria, callback_handler, parameters)

    # now query
    print(f'[eval] evaluating using {ollama.model}')
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
    
    # done
    return res
  
  def evaluate_qa(self, question: str, answer: str, reference: str, overrides: dict) -> dict:

    # log
    print(f'[eval] evaluating {answer[0:64]}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    ollama = Ollama(base_url=self.config.ollama_url(), model=parameters.ollama_model)
    chain = QAEvalChain(ollama, callback_handler)

    # now query
    print(f'[eval] evaluating using {ollama.model}')
    chain.invoke(question, answer, reference)

    # done
    res = callback_handler.to_dict()

    # done
    return res
