#!/usr/bin/env python3

import html
import utils
import config
import requests
from chain_base import ChainParameters
from chain_eval_qa import QAEvalChain
from chain_eval_criteria import CriteriaEvalChain
from chain_qa_base import QAChainBase
from chain_qa_sources import QAChainBaseWithSources
from chain_qa_conversation import QAChainConversational
from callback import CallbackHandler

import langchain
from langchain_community.llms import Ollama
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer, util
from langchain_community.vectorstores import Chroma

class Agent:

  def __init__(self, config):
    if config.debug():
      langchain.verbose = True
      langchain.debug = True
    self.config = config
    self.__build_embedder()
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

  def reverse_embeddings(self, embeddings) -> dict:
    return self.encoder.decode(embeddings)

  def calculate_similarity(self, text1, text2) -> dict:
    model = self.config.embeddings_model()
    e1 = self.encoder.encode(text1)
    e2 = self.encoder.encode(text2)
    if 'paraphrase' in model:
      return util.cos_sim(e1, e2)
    else:
      return util.dot_score(e1, e2)

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

  def query(self, question: str, overrides: dict) -> dict:

    # log
    print(f'[agent] processing {question}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # retriever
    search_kwargs={ 'k': parameters.document_count }
    if parameters.search_type == 'similarity_score_threshold':
      search_kwargs['score_threshold'] = parameters.score_threshold 
    retriever=self.vectorstore.as_retriever(
      search_type=parameters.search_type,
      search_kwargs=search_kwargs
    )
    print(f'[agent] retriever: {retriever.search_type}, {retriever.search_kwargs}')
    
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
    ollama_model = overrides['ollama_model'] if 'ollama_model' in overrides else self.config.ollama_model()
    ollama = Ollama(base_url=self.config.ollama_url(), model=ollama_model)
    chain = self.__build_qa_chain(ollama, retriever, callback_handler, parameters)

    # now query
    print(f'[agent] retrieving and prompting using {ollama.model} and {"custom" if parameters.custom_prompts else "default"} prompts')
    res = chain.invoke(question)

    # extract sources
    sources = self.__build_sources(res, docs)
    callback_handler.set_sources(sources)

    # done
    return callback_handler.to_dict()

  def evaluate_criteria(self, answer: str, criteria: list, overrides: dict) -> dict:

    # log
    print(f'[agent] evaluating {answer[0:64]} against {", ".join(criteria)}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    ollama_model = overrides['ollama_model'] if 'ollama_model' in overrides else self.config.ollama_model()
    ollama = Ollama(base_url=self.config.ollama_url(), model=ollama_model)
    chain = CriteriaEvalChain(ollama, criteria, callback_handler, parameters)

    # now query
    print(f'[agent] evaluating using {ollama.model}')
    chain.invoke(answer)

    # done
    res = callback_handler.to_dict()

    # process answer
    res['evaluation'] = {}
    answer = res['answer']
    ratings = answer.split('\n')
    for rating in ratings:
      try:
        tokens = rating.split(':')
        if len(tokens) == 2:
          criteria_name = tokens[0].strip()
          rating_value = int(tokens[1].split('(')[0])
          res['evaluation'][criteria_name] = rating_value
      except:
        pass

    # make sure we have all criteria
    if len(criteria) != len(res['evaluation'].keys()):
      res['evaluation'] = {}
    
    # done
    return res
  
  def evaluate_qa(self, question: str, answer: str, reference: str, overrides: dict) -> dict:

    # log
    print(f'[agent] evaluating {answer[0:64]}')

    # parse params
    parameters = ChainParameters(self.config, overrides)

    # callback handler
    callback_handler = CallbackHandler(answer, parameters)

    # build chain
    ollama_model = overrides['ollama_model'] if 'ollama_model' in overrides else self.config.ollama_model()
    ollama = Ollama(base_url=self.config.ollama_url(), model=ollama_model)
    chain = QAEvalChain(ollama, callback_handler)

    # now query
    print(f'[agent] evaluating using {ollama.model}')
    chain.invoke(question, answer, reference)

    # done
    res = callback_handler.to_dict()

    # done
    return res
  
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
