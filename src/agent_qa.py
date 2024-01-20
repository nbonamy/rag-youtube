#!/usr/bin/env python3
import os
import json
import html
import utils
from agent_base import AgentBase
from callback import CallbackHandler
from chain_base import ChainParameters
from chain_qa_base import QAChainBase
from chain_qa_sources import QAChainBaseWithSources
from chain_qa_conversation import QAChainConversational
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ConversationSummaryMemory

class AgentQA(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_embedder()
    self._build_vectorstore()
    self._build_database()
    self.__build_memory()
  
  def reset(self):
    self.memory.clear()

  def query(self, question: str, overrides: dict) -> dict:

    # check embeddings consistency
    self.__check_embeddings()

    # log
    print(f'[agent] processing {question}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # we need an llm
    llm = self._build_llm(parameters)

    # we need a retriever
    retriever = self.__build_retriever(llm, parameters)
    
    # debug with similarity_search_with_score
    docs = self.vectorstore.similarity_search_with_score(question, k=parameters.document_count)
    utils.dumpj([ {
      'content': d[0].page_content,
      'source': d[0].metadata['source'],
      'score': d[1]
    } for d in docs], 'relevant_documents.json')

    # # debug with get_relevant_documents
    # docs = retriever.get_relevant_documents(question)
    # print(f'[agent] found {len(docs)} relevant documents')
    # utils.dumpj([ {
    #   'content': d.page_content,
    #   'source': d.metadata['source']
    # } for d in docs], 'relevant_documents.json')

    # callback handler
    callback_handler = CallbackHandler(question, parameters)

    # build chain
    chain = self.__build_qa_chain(llm, retriever, callback_handler, parameters)

    # now query
    print(f'[agent] retrieving and prompting using {"custom" if parameters.custom_prompts else "default"} prompts')
    res = chain.invoke(question)

    # extract sources
    sources = self.__build_sources(res, docs)
    callback_handler.set_sources(sources)

    # save
    try:
      self.database.add_run(callback_handler.to_dict(), 'qa')
    except Exception as e:
      print(f'[agent] failed to save run: {e}')
      pass

    # done
    return callback_handler.to_dict()

  def __build_memory(self):
    memory_type = self.config.memory_type()
    if memory_type == 'buffer':
      self.memory = ConversationBufferMemory(memory_key='chat_history', max_len=50, return_messages=True, output_key='answer')
    elif memory_type == 'buffer_window':
      self.memory = ConversationBufferWindowMemory(memory_key='chat_history', k=5, return_messages=True, output_key='answer')
    elif memory_type == 'summary':
      llm=self._build_llm(ChainParameters(self.config, {}))
      self.memory = ConversationSummaryMemory(llm=llm, memory_key='chat_history', max_len=50, return_messages=True, output_key='answer')
    else:
      raise Exception(f'Unknown memory type "{memory_type}"')

  def __build_retriever(self, llm, parameters: ChainParameters):
    
    # base retriever
    search_kwargs={ 'k': parameters.document_count }
    if parameters.search_type == 'similarity_score_threshold':
      search_kwargs['score_threshold'] = parameters.score_threshold
    base_retriever=self.vectorstore.as_retriever(
      search_type=parameters.search_type,
      search_kwargs=search_kwargs
    )
    print(f'[agent] base retriever: {base_retriever.search_type}, {base_retriever.search_kwargs}')

    # final retriever
    if parameters.retriever_type == 'base':
      return base_retriever
    elif parameters.retriever_type == 'multi_query':
      print(f'[agent] building multi query retriever')
      return MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
      )
    elif parameters.retriever_type == 'compressor':
      print(f'[agent] building compressor retriever')
      compressor=LLMChainExtractor.from_llm(llm)
      return ContextualCompressionRetriever(
        base_retriever=base_retriever,
        base_compressor=compressor,
      )
    else:
      raise Exception(f'Unknown retriever type "{self.config.retriever_type()}"')

  def __build_qa_chain(self, llm, retriever, callback, parameters: ChainParameters):
    if parameters.chain_type == 'base':
      return QAChainBase(llm, retriever, callback, parameters)
    elif 'source' in parameters.chain_type:
      return QAChainBaseWithSources(llm, retriever, callback, parameters)
    elif 'conversation' in parameters.chain_type:
      return QAChainConversational(llm, retriever, self.memory, callback, parameters)
    else:
      raise Exception(f'Chain type "{parameters.chain_type}" not in base, base_with_sources, conversation')

  def __build_sources(self, result, docs) -> list:

    # we need to do it in diffrerent ways depending on the chain type
    # but also beccause RetrievalQAWithSourcesChain does not seem to be
    # super consistent in how it returns sources

    # extract video ids
    video_ids = []
    if 'sources' in result.keys() and len(result['sources']) > 0:
      print('[agent] extracting sources from "sources"')
      video_ids.extend([s.strip() for s in result['sources'].split(',')])

    # finally documents returned by retriever
    if len(video_ids) == 0 and 'source_documents' in result.keys():
      print('[agent] extracting sources from "source_documents"')
      for source in result['source_documents']:
        video_ids.append(source.metadata['source'])

    # now build our sources
    sources = {}
    relevance_score_fn = self.vectorstore._select_relevance_score_fn()
    for video_id in video_ids:

      # get video info
      if video_id not in sources.keys():
        video_info = utils.get_video_info(video_id)
        if video_info is not None:
          sources[video_id] = {
            'id': video_id,
            'url': utils.get_video_url(video_id),
            'title': html.unescape(video_info['snippet']['title'])
          }

      # now get score
      if video_id in sources.keys() and docs is not None:
        for doc in docs:
          if doc[0].metadata['source'] == video_id:
            score = relevance_score_fn(doc[1])
            if 'score' in sources[video_id].keys():
              sources[video_id]['score'] = min(sources[video_id]['score'], score)
            else:
              sources[video_id]['score'] = score
            break

    return list(sources.values())

  def __check_embeddings(self):
    if os.path.exists('db_config.json'):
      with open('db_config.json', 'r') as f:
        db_config = json.load(f)
        db_embeddings = db_config['embeddings_model']
        cfg_embeddings = self.config.embeddings_model()
        if db_embeddings != cfg_embeddings:
          raise Exception(f'Embeddings model mismatch: {db_embeddings} != {cfg_embeddings}')
