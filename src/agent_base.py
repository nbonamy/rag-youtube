#!/usr/bin/env python3
import config
import requests
import langchain
from chain_base import ChainParameters
from langchain_community.llms import Ollama
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings, HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer, util
from langchain_community.vectorstores import Chroma

class AgentBase:

  def __init__(self, config):
    if config.debug():
      langchain.verbose = True
      langchain.debug = True
    self.config = config
    self.embeddings = None
    self.vectorstore = None
  
  def list_ollama_models(self) -> dict:
    url = f'{self.config.ollama_url()}/api/tags'
    return requests.get(url).json()

  def calculate_embeddings(self, text) -> dict:
    return self.encoder.encode(text)

  def calculate_similarity(self, text1, text2) -> dict:
    model = self.config.embeddings_model()
    e1 = self.encoder.encode(text1)
    e2 = self.encoder.encode(text2)
    if 'paraphrase' in model:
      return util.cos_sim(e1, e2)
    else:
      return util.dot_score(e1, e2)

  def _build_embedder(self) -> None:
    if self.embeddings is not None:
      return
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

  def _build_vectorstore(self) -> None:
    if self.vectorstore is not None:
      return
    if self.embeddings is None:
      self._build_embedder()
    self.vectorstore=Chroma(persist_directory=self.config.db_persist_directory(), embedding_function=self.embeddings)

  def _build_llm(self, parameters: ChainParameters) -> Ollama:
    return Ollama(
      base_url=self.config.ollama_url(),
      model=parameters.ollama_model,
      temperature=parameters.llm_temperature,
    )
