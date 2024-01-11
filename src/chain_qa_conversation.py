
from chain_base import ChainBase
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain

PROMPT="""Use the following pieces of context to answer the question at the end.
If the question is not directly related to the context, just say that you don't know, don't try to make up an answer. 
If not enough information is available in the context, just say that you don't know, don't try to make up an answer.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
In any case, please do not leverage your own knowledge.

{context}

{chat_history}
Question: {question}
Helpful Answer:"""

class QAChainConversational(ChainBase):
  
    chain = None
    
    @staticmethod
    def build(llm, retriever, memory, chain_type):
    
      if QAChainConversational.chain is None:
      
        # build prompt
        prompt = PromptTemplate(input_variables=['context', 'chat_history', 'question'], template=PROMPT)
        
        # build chain
        print(f'[chain] building conversational retrieval chain of type {chain_type}')
        chain = ConversationalRetrievalChain.from_llm(
          llm=llm,
          chain_type=chain_type,
          retriever=retriever,
          memory=memory,
          return_source_documents=True,
          #combine_docs_chain_kwargs={ 'prompt': prompt },
        )
        ChainBase.dump_chain_prompts(chain)
        QAChainConversational.chain = chain

      # done
      return (QAChainConversational.chain, 'question')
