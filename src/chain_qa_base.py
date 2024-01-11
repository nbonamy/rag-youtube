
from chain_base import ChainBase
from langchain.chains import RetrievalQA

class QAChainBase(ChainBase):

  def __init__(self, llm, retriever, config):

    # build chain
    chain_type = config.doc_chain_type()
    print(f'[chain] building basic retrieval chain of type {chain_type}')
    self.chain = RetrievalQA.from_chain_type(
      llm=llm,
      chain_type=chain_type,
      retriever=retriever,
      return_source_documents=config.return_sources(),
      chain_type_kwargs=self._get_prompt_kwargs(config),
    )
    self._dump_chain_prompts()

  def invoke(self, prompt):
    return self.chain.invoke({ 'query': prompt })
