
from chain_base import ChainBase
from langchain.chains import RetrievalQAWithSourcesChain

class QAChainBaseWithSources(ChainBase):

  chain = None

  @staticmethod
  def build(llm, retriever, chain_type):

    # build chain
    if QAChainBaseWithSources.chain is None:
      print(f'[chain] building retrieval chain with sources of type {chain_type}')
      chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type=chain_type,
        retriever=retriever,
        #return_source_documents=True,
      )
      ChainBase.dump_chain_prompts(chain)
      QAChainBaseWithSources.chain = chain

    # done
    return (QAChainBaseWithSources.chain, 'question')
