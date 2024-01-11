
from chain_base import ChainBase
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts import PromptTemplate

PROMPT_QUESTION="""Given the following extracted parts of several source documents and a question, create a final answer with references.
If the question is not directly related to the context, just say that you don't know, don't try to make up an answer. 
If not enough information is available in the context, just say that you don't know, don't try to make up an answer.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
In any case, please do not leverage your own knowledge.
Each source document is made of a "Content" section and a "Source" section which is what you should use to refer to that source. 
ALWAYS return a "SOURCES" part at the end of your answer which is a comma separated list of sources that you see as relevant.

SOURCES:
{summaries}

QUESTION: {question}

FINAL ANSWER:"""

class QAChainBaseWithSources(ChainBase):

  def __init__(self, llm, retriever, config):

    super().__init__()

    # build chain
    chain_type = config.doc_chain_type()
    print(f'[chain] building retrieval chain with sources of type {chain_type}')
    self.chain = RetrievalQAWithSourcesChain.from_chain_type(
      llm=llm,
      chain_type=chain_type,
      retriever=retriever,
      #return_source_documents=config.return_sources(),
      chain_type_kwargs=self._get_prompt_kwargs(config),
    )
    self._dump_chain_prompts()

  def invoke(self, prompt):
    return self.chain.invoke({ 'question': prompt })

  def _get_prompt_kwargs(self, config):
    if not config.use_custom_prompts() or config.doc_chain_type() != 'stuff':
      return super()._get_prompt_kwargs(config)
  
    prompt = PromptTemplate(input_variables=['summaries', 'question'], template=PROMPT_QUESTION)
    return { 'prompt': prompt }
