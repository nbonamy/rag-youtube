
from chain_base import ChainBase, ChainParameters
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate

class QAChainBaseWithSources(ChainBase):

  def __init__(self, llm, retriever, callback, parameters: ChainParameters):

    # save callback
    self.callback = callback
    
    # build chain
    print(f'[chain] building retrieval chain with sources of type {parameters.doc_chain_type}')
    self.chain = RetrievalQAWithSourcesChain.from_chain_type(
      llm=llm,
      chain_type=parameters.doc_chain_type,
      retriever=retriever,
      #return_source_documents=config.return_sources(),
      chain_type_kwargs=self._get_prompt_kwargs(parameters),
    )

  def _get_prompt_kwargs(self, parameters):
    if not parameters.custom_prompts or parameters.doc_chain_type != 'stuff':
      return super()._get_prompt_kwargs(parameters)
  
    with open('prompts/sourced.txt', 'r') as f:
      prompt = PromptTemplate(input_variables=['summaries', 'question'], template=f.read())
      return { 'prompt': prompt }
