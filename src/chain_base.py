
import utils
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

class ChainParameters:
  def __init__(self, config, overrides):
    self.ollama_model = overrides['ollama_model'] if 'ollama_model' in overrides else config.ollama_model()
    self.chain_type = overrides['chain_type'] if 'chain_type' in overrides else config.chain_type()
    self.doc_chain_type = overrides['doc_chain_type'] if 'doc_chain_type' in overrides else config.doc_chain_type()
    self.search_type = overrides['search_type'] if 'search_type' in overrides else config.search_type()
    self.score_threshold = float(overrides['score_threshold']) if 'score_threshold' in overrides else config.score_threshold()
    self.document_count = int(overrides['document_count']) if 'document_count' in overrides else config.document_count()
    self.custom_prompts = utils.is_true(overrides['custom_prompts']) if 'custom_prompts' in overrides else config.custom_prompts()
    self.return_sources = utils.is_true(overrides['return_sources']) if 'return_sources' in overrides else config.return_sources()

  def to_dict(self):
    return {
      'ollama_model': self.ollama_model,
      'chain_type': self.chain_type,
      'doc_chain_type': self.doc_chain_type,
      'search_type': self.search_type,
      'score_threshold': self.score_threshold,
      'document_count': self.document_count,
      'custom_prompts': self.custom_prompts,
      'return_sources': self.return_sources,
    }

class ChainBase:

  def __init__(self):
    self.chain = None
    self.callback = None

  def invoke(self, prompt: str):
    return self.chain.invoke(
      input={ self._get_input_key(): prompt },
      config=RunnableConfig(callbacks=[self.callback])
    )

  def _get_input_key(self):
    return 'question'
  
  def _get_prompt_kwargs(self, parameters: ChainParameters):
    if parameters.custom_prompts:
      if parameters.doc_chain_type == 'stuff':
        return { 'prompt': self._get_question_prompt() }
      elif parameters.doc_chain_type == 'map_reduce':
        return {
          'question_prompt': self._get_question_prompt(),
          'combine_prompt': self._get_combine_prompt(),
        }
    return {}
  
  def _get_question_prompt(self):
    with open('prompts/base.txt', 'r') as f:
      return PromptTemplate(input_variables=['context', 'question'], template=f.read())

  def _get_combine_prompt(self):
    with open('prompts/combine.txt', 'r') as f:
      return PromptTemplate(input_variables=['summaries', 'question'], template=f.read())

  def _dump_chain_prompts(self):

    try:

      # we need a chain
      prompts = {}
      if self.chain is None:
        return
      
      # base prompt
      try:
        prompts['chain'] = self.chain.prompt.template
      except:
        pass

      # generator
      try:
        prompts['generator'] = self.chain.question_generator.prompt.template
      except:
        pass

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

      # combine chain
      if combine_chain is not None:
        
        # llm
        prompts['llm'] = combine_chain.llm_chain.prompt.template,

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
      
      # dump
      utils.dumpj(prompts, 'chain_templates.json')

    except:
      print('[chain] failed to dump chain prompts')
      pass