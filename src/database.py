#!/usr/bin/env python3

import os
import html
import utils
import config
import requests
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema.document import Document
from langchain.callbacks.base import BaseCallbackHandler
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from sentence_transformers import SentenceTransformer

PROMPT="""Use the following pieces of context to answer the question at the end.
If the question is not directly related to the context, just say that you don't know, don't try to make up an answer. 
If not enough information is available in the context, just say that you don't know, don't try to make up an answer.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
In any case, please do not leverage your own knowledge.

{context}

{chat_history}
Question: {question}
Helpful Answer:"""

class Database:

  def __init__(self, config):
    self.config = config
    self.__build_embedder()
    self.stream_handler = StreamHandler()
    self.ollama = Ollama(base_url=config.ollama_url(), model=config.ollama_model(), callbacks=[self.stream_handler])
    self.vectorstore = Chroma(persist_directory=config.persist_directory(), embedding_function=self.embeddings)
    self.splitter = RecursiveCharacterTextSplitter(chunk_size=config.split_chunk_size(), chunk_overlap=config.split_chunk_overlap())
    self.memory = ConversationBufferMemory(memory_key='chat_history', max_len=50, return_messages=True, output_key='answer')
  
  def __build_embedder(self):
    model = self.config.embeddings_model()
    print(f'[database] building embeddings for {model}')
    if model == 'ollama':
      self.encoder = None
      self.embeddings = OllamaEmbeddings(base_url=config.ollama_url(), model=config.ollama_model())
    elif model.startswith('openai:'):
      self.encoder = None
      self.embeddings = OpenAIEmbeddings(model=model.split(':')[1])
    else:
      self.encoder = SentenceTransformer(model)
      self.embeddings = HuggingFaceEmbeddings(model_name=model)

  def list_ollama_models(self) -> dict:
    url = f'{self.config.ollama_url()}/api/tags'
    return requests.get(url).json()

  def calculate_embeddings(self, text) -> dict:
    return self.encoder.encode(text)

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
    self.vectorstore = Chroma.from_documents(
      documents=all_splits,
      embedding=self.embeddings,
      persist_directory=self.config.persist_directory()
    )

    # done
    self.vectorstore.persist()
    return

  def query(self, question) -> dict:

    # log
    print(f'[database] processing {question}')

    # retriever
    retriever=self.vectorstore.as_retriever(
      search_type='similarity',
      search_kwargs={
        'k': self.config.similarity_document_count(),
      }
    )
    print(f'[database] retriever: {retriever.search_type}, {retriever.search_kwargs}')
    
    # debug with similarity_search_with_score
    docs = self.vectorstore.similarity_search_with_score(question, k=self.config.similarity_document_count())
    utils.dumpj([ {
      'content': d[0].page_content,
      'source': d[0].metadata['source'],
      'score': d[1]
    } for d in docs], 'relevant_documents.json')

    # # debug with get_relevant_documents
    # docs = retriever.get_relevant_documents(question)
    # print(f'[database] found {len(docs)} relevant documents')
    # utils.dumpj([ {
    #   'content': d.page_content,
    #   'source': d.metadata['source']
    # } for d in docs], 'relevant_documents.json')

    # build chain
    (qachain, key) = self.__build_qa_chain(retriever)

    # now query
    print('[database] retrieving')
    res = qachain({key: question})

    # extract sources
    sources = self.__build_sources(res['source_documents'], docs)
    self.stream_handler.set_sources(sources)

    # done
    return self.stream_handler.output()

  def __build_qa_chain(self, retriever):
    if self.config.conversational_chain():
      return self.__build_convesational_qa_chain(retriever)
    else:
      return self.__build_base_qa_chain(retriever)

  def __build_base_qa_chain(self, retriever):

    # build prompt
    prompt = PromptTemplate(input_variables=['context', 'question'], template=PROMPT.replace('{chat_history}', ''))
    
    # build chain
    print('[database] building basic retrieval chain')
    qachain = RetrievalQA.from_chain_type(
      llm=self.ollama,
      chain_type='stuff',
      retriever=retriever,
      return_source_documents=True,
      chain_type_kwargs={ 'prompt': prompt },
    )
    utils.dumpj(qachain.combine_documents_chain.llm_chain.prompt.template, 'chain_template.json')

    # done
    return (qachain, 'query')

  def __build_convesational_qa_chain(self, retriever):

    # build prompt
    prompt = PromptTemplate(input_variables=['context', 'chat_history', 'question'], template=PROMPT)
    
    # build chain
    print('[database] building conversational retrieval chain')
    qachain = ConversationalRetrievalChain.from_llm(
      llm=self.ollama,
      chain_type='stuff',
      retriever=retriever,
      memory=self.memory,
      return_source_documents=True,
      combine_docs_chain_kwargs={ 'prompt': prompt },
    )
    utils.dumpj(qachain.combine_docs_chain.llm_chain.prompt.template, 'chain_template.json')

    # done
    return (qachain, 'question')

  def __build_sources(self, source_docs, docs) -> list:

    sources = {}
    for source in source_docs:
      video_id = source.metadata['source']
      if video_id in sources.keys():
        continue
      video_info = utils.get_video_info(video_id)
      if video_info is not None:
        sources[video_id] = {
          'id': video_id,
          'url': f'https://www.youtube.com/watch?v={video_id}',
          'title': html.unescape(video_info['snippet']['title'])
        }
        if docs is not None:
          for doc in docs:
            if doc[0].metadata['source'] == video_id:
              if 'score' in sources[video_id].keys():
                sources[video_id]['score'] = min(sources[video_id]['score'], doc[1])
              else:
                sources[video_id]['score'] = doc[1]
              break

    return list(sources.values())

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

  def set_sources(self, sources: list) -> None:
    self.sources = sources

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