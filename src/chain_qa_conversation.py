
from chain_base import ChainBase
from langchain.chains import ConversationalRetrievalChain

class QAChainConversational(ChainBase):
  
  def __init__(self, llm, retriever, memory, config):
  
    # build chain
    chain_type = config.doc_chain_type()
    print(f'[chain] building conversational retrieval chain of type {chain_type}')
    self.chain = ConversationalRetrievalChain.from_llm(
      llm=llm,
      chain_type=chain_type,
      retriever=retriever,
      memory=memory,
      #return_source_documents=True,
      combine_docs_chain_kwargs=self._get_prompt_kwargs(config),
    )
    self._dump_chain_prompts()

  def invoke(self, prompt):
    return self.chain.invoke({ 'question': prompt })
