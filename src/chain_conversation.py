
import utils
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

class QAChainConversational:
  
    @staticmethod
    def build(llm, retriever, memory):
    
      # build prompt
      prompt = PromptTemplate(input_variables=['context', 'chat_history', 'question'], template=PROMPT)
      
      # build chain
      print('[chain] building conversational retrieval chain')
      qachain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={ 'prompt': prompt },
      )
      utils.dumpj(qachain.combine_docs_chain.llm_chain.prompt.template, 'chain_template.json')

      # done
      return (qachain, 'question')
