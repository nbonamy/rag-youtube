
import utils
from langchain.prompts import PromptTemplate

PROMPT_QUESTION="""HELLO. Use the following pieces of context to answer the question at the end.
If the question is not directly related to the context, just say that you don't know, don't try to make up an answer. 
If not enough information is available in the context, just say that you don't know, don't try to make up an answer.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
In any case, please do not leverage your own knowledge.

{context}

Question: {question}
Helpful Answer:"""

PROMPT_COMBINE="""HELLO. Given the following extracted parts of a long document and a question, create a final answer.
If you don't know the answer, just say that you don't know. Don't try to make up an answer.

QUESTION: {question}
=========
{summaries}
=========

FINAL ANSWER:"""

class ChainBase:

  def __init__(self):
    self.chain = None

  def invoke(self, _):
    raise NotImplementedError()
  
  def _get_prompt_kwargs(self, config):
    if config.use_custom_prompts():
      if config.doc_chain_type() == 'stuff':
        return { 'prompt': self._get_question_prompt() }
      elif config.doc_chain_type() == 'map_reduce':
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