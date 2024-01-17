#!/usr/bin/env python3
from agent_base import AgentBase
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

class Loader(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_embedder()
    self._build_vectorstore()
    self.splitter = RecursiveCharacterTextSplitter(
      chunk_size=config.split_chunk_size(),
      chunk_overlap=config.split_chunk_overlap()
    )

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
