
import utils
from langchain.prompts import PromptTemplate

PROMPT_QUESTION="""Use the following pieces of context to answer the question at the end.
If the question is not directly related to the context, just say that you don't know, don't try to make up an answer. 
If not enough information is available in the context, just say that you don't know, don't try to make up an answer.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
In any case, please do not leverage your own knowledge.

{context}

Question: {question}
Helpful Answer:"""

PROMPT_COMBINE="""Given the following extracted parts of a long document and a question, create a final answer.
If you don't know the answer, just say that you don't know. Don't try to make up an answer.

QUESTION: {question}
=========
{summaries}
=========

FINAL ANSWER:"""

class ChainParameters:
  def __init__(self, config, overrides):
    self.chain_type = overrides['chain_type'] if 'chain_type' in overrides else config.chain_type()
    self.doc_chain_type = overrides['doc_chain_type'] if 'doc_chain_type' in overrides else config.doc_chain_type()
    self.search_type = overrides['search_type'] if 'search_type' in overrides else config.search_type()
    self.document_count = int(overrides['document_count']) if 'document_count' in overrides else config.similarity_document_count()
    self.custom_prompts = utils.is_true(overrides['custom_prompts']) if 'custom_prompts' in overrides else config.custom_prompts()
    self.return_sources = utils.is_true(overrides['return_sources']) if 'return_sources' in overrides else config.return_sources()

  def to_dict(self):
    return {
      'chain_type': self.chain_type,
      'doc_chain_type': self.doc_chain_type,
      'search_type': self.search_type,
      'custom_prompts': self.custom_prompts,
      'document_count': self.document_count,
      'return_sources': self.return_sources,
    }

class ChainBase:

  def __init__(self):
    self.chain = None

  def invoke(self, _):
    raise NotImplementedError()
  
  def _get_prompt_kwargs(self, parameters: ChainParameters):
    if parameters.custom_prompts:
      if parameters.doc_chain_type == 'stuff':
        return { 'prompt': self._get_question_prompt() }
      elif parameters.doc_chain_type == 'map_reduce':
        return {
          'question_prompt': self._get_question_prompt(),
          'combine_prompt': self._get_combine_prompt(),
        }
    return None
  
  def _get_question_prompt(self):
    return PromptTemplate(input_variables=['context', 'question'], template=PROMPT_QUESTION)

  def _get_combine_prompt(self):
    return PromptTemplate(input_variables=['summaries', 'question'], template=PROMPT_COMBINE)

  def _dump_chain_prompts(self):

    try:

      # we need a chain
      if self.chain is None:
        return

      # find the combine chain
      combine_chain = None
      try:
        combine_chain = self.chain.combine_documents_chain
      except:
        pass
      if combine_chain is None:
        try:
          combine_chain = self.chain.combine_docs_chain
        except:
          pass
      if combine_chain is None:
        return

      # llm
      prompts = {
        'llm': combine_chain.llm_chain.prompt.template,
      }

      # collapse
      try:
        prompts['collapse'] = combine_chain.collapse_document_chain.llm_chain.prompt.template
      except:
        pass

      # combine
      try:
        prompts['combine'] = combine_chain.combine_document_chain.llm_chain.prompt.template
      except:
        pass
      
      # generator
      try:
        prompts['generator'] = self.chain.question_generator.prompt.template
      except:
        pass

      # dump
      utils.dumpj(prompts, 'chain_templates.json')

    except:
      print('[chain] failed to dump chain prompts')
      pass