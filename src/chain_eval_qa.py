
from chain_base import ChainBase
from langchain.evaluation.qa.eval_chain import QAEvalChain as LCQAEvalChain
from langchain_core.runnables import RunnableConfig

#
# default prompts
# https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/evaluation/qa/eval_prompt.py
#

class QAEvalChain(ChainBase):

  def __init__(self, llm, callback):

    # save stuff
    self.callback = callback
    
    # build chain
    print(f'[chain] building llm evaluation chain')
    self.chain = LCQAEvalChain.from_llm(llm=llm)

  def invoke(self, question, answer, reference):
    self.callback.templates = self._get_chain_prompt_templates()
    return self.chain.invoke(input={
      'query': question,
      'result': answer,
      'answer': reference,
    }, config=RunnableConfig(callbacks=[self.callback])
)
