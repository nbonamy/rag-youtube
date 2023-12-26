
import utils
from langchain.chains import RetrievalQAWithSourcesChain

class QAChainBaseWithSources:

  chain = None

  @staticmethod
  def build(llm, retriever):

    # build chain
    if QAChainBaseWithSources.chain is None:
      print('[chain] building retrieval chain with sources')
      chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        return_source_documents=True,
      )
      utils.dumpj(chain.combine_documents_chain.llm_chain.prompt.template, 'chain_template.json')
      QAChainBaseWithSources.chain = chain

    # done
    return (QAChainBaseWithSources.chain, 'question')
