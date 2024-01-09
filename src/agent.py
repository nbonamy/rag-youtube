#!/usr/bin/env python3

import os
import html
import utils
import config
import requests
from chain_base import QAChainBase
from chain_base_source import QAChainBaseWithSources
from chain_conversation import QAChainConversational
from stream_handler import StreamHandler

import langchain
from langchain_community.llms import Ollama
from langchain.schema.document import Document
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from sentence_transformers import SentenceTransformer

class Agent:

  def __init__(self, config):
    if config.debug():
      langchain.verbose = True
      langchain.debug = True
    self.config = config
    self.__build_embedder()
    self.stream_handler = StreamHandler()
    self.ollama = Ollama(base_url=config.ollama_url(), model=config.ollama_model(), callbacks=[self.stream_handler])
    self.vectorstore = Chroma(persist_directory=config.db_persist_directory(), embedding_function=self.embeddings)
    self.splitter = RecursiveCharacterTextSplitter(chunk_size=config.split_chunk_size(), chunk_overlap=config.split_chunk_overlap())
    self.memory = ConversationBufferMemory(memory_key='chat_history', max_len=50, return_messages=True, output_key='answer')
  
  def reset(self):
    self.memory.clear()

  def list_ollama_models(self) -> dict:
    url = f'{self.config.ollama_url()}/api/tags'
    return requests.get(url).json()

  def calculate_embeddings(self, text) -> dict:
    return self.encoder.encode(text)

  def add_text(self, content, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    #print('[agent] splitting text')
    all_splits = self.splitter.split_text(content)
    metadatas = [metadata] * len(all_splits)
    
    # create embeddings
    #print('[agent] creating embeddings')
    self.vectorstore.add_texts(all_splits, metadatas=metadatas)

    # done
    self.vectorstore.persist()
    return

  def add_documents(self, documents, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    #print('[agent] splitting text')
    all_splits = self.splitter.split_documents(documents)

    # create embeddings
    #print('[agent] creating embeddings')
    self.vectorstore = Chroma.from_documents(
      documents=all_splits,
      embedding=self.embeddings,
      persist_directory=self.config.db_persist_directory()
    )

    # done
    self.vectorstore.persist()
    return

  def query(self, question) -> dict:

    # log
    print(f'[agent] processing {question}')

    # retriever
    retriever=self.vectorstore.as_retriever(
      search_type='similarity',
      search_kwargs={
        'k': self.config.similarity_document_count(),
      }
    )
    print(f'[agent] retriever: {retriever.search_type}, {retriever.search_kwargs}')
    
    # debug with similarity_search_with_score
    docs = self.vectorstore.similarity_search_with_score(question, k=self.config.similarity_document_count())
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

    # build chain
    (qachain, key) = self.__build_qa_chain(retriever)

    # now query
    print('[agent] retrieving')
    res = qachain({key: question})

    # extract sources
    sources = self.__build_sources(res, docs, self.config.max_source_score())
    self.stream_handler.set_sources(sources)

    # done
    return self.stream_handler.output()

  def __build_embedder(self):
    model = self.config.embeddings_model()
    print(f'[agent] building embeddings for {model}')
    if model == 'ollama':
      self.encoder = None
      self.embeddings = OllamaEmbeddings(base_url=config.ollama_url(), model=config.ollama_model())
    elif model.startswith('openai:'):
      self.encoder = None
      self.embeddings = OpenAIEmbeddings(model=model.split(':')[1])
    else:
      self.encoder = SentenceTransformer(model)
      self.embeddings = HuggingFaceEmbeddings(model_name=model)

  def __build_qa_chain(self, retriever):
    chain_type = self.config.chain_type()
    if chain_type == 'base':
      return QAChainBase.build(self.ollama, retriever)
    elif chain_type == 'base_with_sources' or chain_type == 'base_sourced':
      return QAChainBaseWithSources.build(self.ollama, retriever)
    elif chain_type == 'conversation' or chain_type == 'conversational':
      return QAChainConversational.build(self.ollama, retriever, self.memory)
    else:
      raise Exception(f'Chain type "{chain_type}" not in base, base_with_sources, conversation')

  def __build_sources(self, result, docs, max_score) -> list:

    # we need to do it in diffrerent ways depending on the chain type
    # but also beccause RetrievalQAWithSourcesChain does not seem to be
    # super consistent in how it returns sources

    # extract video ids
    video_ids = []
    if 'sources' in result.keys() and len(result['sources']) > 0:
      print('[agent] extracting sources from "sources"')
      video_ids.extend([s.strip() for s in result['sources'].split(',')])

    # try in text
    if len(video_ids) == 0 and 'answer' in result.keys() or 'result' in result.keys():
      answer = result['answer'] if 'answer' in result.keys() else result['result']
      if 'SOURCES:' in answer:
        print('[agent] extracting sources from "answer"')
        video_ids.extend([s.strip() for s in result['answer'].split('SOURCES:')[1].split(',')])

    # finally documents returned by retriever
    if len(video_ids) == 0 and 'source_documents' in result.keys():
      print('[agent] extracting sources from "source_documents"')
      for source in result['source_documents']:
        video_ids.append(source.metadata['source'])

    # now build our sources
    sources = {}
    for video_id in video_ids:
      if video_id not in sources.keys():
        video_info = utils.get_video_info(video_id)
        if video_info is not None:
          sources[video_id] = {
            'id': video_id,
            'url': utils.get_video_url(video_id),
            'title': html.unescape(video_info['snippet']['title'])
          }
      if video_id in sources.keys() and docs is not None:
        for doc in docs:
          if doc[0].metadata['source'] == video_id:
            score = doc[1]
            if 'score' in sources[video_id].keys():
              sources[video_id]['score'] = min(sources[video_id]['score'], score)
            else:
              sources[video_id]['score'] = score
            break

    return list(filter(lambda source: 'score' not in source or max_score == 0.0 or source['score'] < max_score, sources.values()))
