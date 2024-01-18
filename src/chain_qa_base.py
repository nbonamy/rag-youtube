
from chain_base import ChainBase, ChainParameters
from langchain.chains import RetrievalQA

class QAChainBase(ChainBase):

  def __init__(self, llm, retriever, callback, parameters: ChainParameters):

    # save callback
    self.callback = callback
    
    # build chain
    print(f'[chain] building basic retrieval chain of type {parameters.doc_chain_type}')
    self.chain = RetrievalQA.from_chain_type(
      llm=llm,
      chain_type=parameters.doc_chain_type,
      retriever=retriever,
      return_source_documents=parameters.return_sources,
      chain_type_kwargs=self._get_prompt_kwargs(parameters)
    )

  def _get_input_key(self):
    return 'query'
