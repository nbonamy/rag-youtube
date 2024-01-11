
import utils

class ChainBase:

  @staticmethod
  def dump_chain_prompts(chain):

    try:

      # find the combine chain
      combine_chain = None
      try:
        combine_chain = chain.combine_documents_chain
      except:
        pass
      if combine_chain is None:
        try:
          combine_chain = chain.combine_docs_chain
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
        prompts['generator'] = chain.question_generator.prompt.template
      except:
        pass

      # dump
      utils.dumpj(prompts, 'chain_templates.json')

    except:
      print('[chain] failed to dump chain prompts')
      pass