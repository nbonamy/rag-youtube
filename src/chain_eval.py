
from chain_base import ChainBase, ChainParameters
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

PROMPT_EVALUATE="""Rate the following text on the following criteria: {criteria}.
Rate each criteria on a scale from 1 to 5, where 1 is the lowest and 5 is the highest.
Rate each criteria independently of the others. For instance helpfulness should be rated independently of relevance.
Only provide the numerical ratings, do not provide any additional text or explanation.
If the text is too short, rate it anyway.

For example if the criteria are helpful, detailed and harmless then your answer should look like this:
Helpful: 5
Detailed: 4
Harmless: 3

Notice how there is no additional text!

TEXT:
{question}

RATING:"""

class EvalChain(ChainBase):

  def __init__(self, llm, criteria:list, callback, parameters: ChainParameters):

    # save stuff
    self.callback = callback
    
    # build chain
    print(f'[chain] building llm evaluation chain')
    self.chain = LLMChain(llm=llm, prompt=self._get_prompt(criteria))
    self._dump_chain_prompts()

  def _get_prompt(self, criteria):

    template = PROMPT_EVALUATE.replace('{criteria}', ', '.join(criteria))
    return PromptTemplate(
      input_variables=['question'],
      template=template
    )
