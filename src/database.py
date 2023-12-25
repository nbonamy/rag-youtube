#!/usr/bin/env python3

import os
import utils
import config
import requests
from langchain.llms import Ollama
from langchain.schema.document import Document
from langchain.callbacks.base import BaseCallbackHandler
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.vectorstores import Chroma, FAISS

class Database:

  def __init__(self, config):
    self.base_url = config.ollama_url()
    self.model = config.ollama_model()
    self.persist_directory = config.persist_directory()
    self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # self.embeddings = OpenAIEmbeddings(model='text-search-ada-doc-001')
    # self.embeddings = OllamaEmbeddings(base_url=self.base_url, model=self.model)
    self.stream_handler = StreamHandler()
    self.ollama = Ollama(base_url=self.base_url, model=self.model, callbacks=[self.stream_handler])
    self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
    self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  
  def list_ollama_models(self) -> dict:
    url = f'{self.base_url}/api/tags'
    return requests.get(url).json()

  def query(self, question) -> dict:

    # log
    print(f'[database] processing {question}')

    # retriever
    retriever=self.vectorstore.as_retriever(search_type='similarity', search_kwargs={'k': 4})
    
    # # debug
    # docs = self.vectorstore.similarity_search_with_score(question)
    # print([doc[0].metadata['source'] for doc in docs])

    # # debug
    # print(f'[database] retriever: {retriever.search_type}, {retriever.search_kwargs}')
    # docs = retriever.get_relevant_documents(question)
    # print(f'[database] found {len(docs)} relevant documents')
    # print([doc.metadata['source'] for doc in docs])

    # now query
    print('[database] retrieving')
    qachain = RetrievalQA.from_chain_type(self.ollama, chain_type='stuff', retriever=retriever, return_source_documents=True)
    #print(qachain.combine_documents_chain.llm_chain.prompt.template)
    res = qachain({"query": question, "question": question})

    # extract sources
    sources = {}
    for doc in res['source_documents']:
      video_id = doc.metadata['source']
      if video_id in sources.keys():
        continue
      video_info = utils.get_video_info(video_id)
      if video_info is not None:
        sources[video_id] = {
          'id': video_id,
          'url': f'https://www.youtube.com/watch?v={video_id}',
          'title': video_info['snippet']['title']
        }
    self.stream_handler.set_sources(sources.values())

    # done
    return self.stream_handler.output()
    
  def add_text(self, content, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    print('[database] splitting text')
    all_splits = self.splitter.split_text(content)
    metadatas = [metadata] * len(all_splits)
    
    # create database
    print('[database] creating embeddings')
    self.vectorstore.add_texts(all_splits, metadatas=metadatas)

    # done
    self.vectorstore.persist()
    return

  def add_documents(self, documents, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    print('[database] splitting text')
    all_splits = self.splitter.split_documents(documents)

    # create embeddings
    print('[database] creating embeddings')
    self.vectorstore = Chroma.from_documents(documents=all_splits, embedding=self.embeddings, persist_directory=self.persist_directory)

    # done
    self.vectorstore.persist()
    return

class StreamHandler(BaseCallbackHandler):
  def __init__(self):
    self.reset()

  def reset(self):
    self.created = utils.now()
    self.text = None
    self.sources = []
    self.start = None
    self.end = None
    self.tokens = 0

  def set_sources(self, sources) -> None:
    self.sources = list(sources)

  def on_llm_start(self, serialized: dict, prompts: dict, **kwargs) -> None:
    print('[database] llm starting')
    self.reset()
  
  def on_llm_new_token(self, token: str, **kwargs) -> None:
    if self.text is None:
      self.text = token
      self.start = utils.now()
      self.end = utils.now()
      self.tokens = 1
    else:
      self.text += token
      self.tokens += 1
      self.end = utils.now()

  def time_1st_token(self) -> float:
    return self.start - self.created

  def tokens_per_sec(self)  -> float:
    return self.tokens / (self.end - self.start) * 1000

  def output(self) -> dict:
    return {
      'text': self.text.strip(),
      'sources': self.sources,
      'performance': {
        'tokens': self.tokens,
        'time_1st_token': int(self.time_1st_token()),
        'tokens_per_sec': round(self.tokens_per_sec(), 2)
      }
    }