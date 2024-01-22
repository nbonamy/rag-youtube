#!/usr/bin/env python3
import requests

# get tokens
# select sum(json_extract(trace, '$.performance.input_tokens'))+ sum(json_extract(evaluation_crit_trace, '$.performance.input_tokens'))+ sum(json_extract(evaluation_qa_trace, '$.performance.input_tokens')), sum(json_extract(trace, '$.performance.output_tokens'))+ sum(json_extract(evaluation_crit_trace, '$.performance.output_tokens'))+ sum(json_extract(evaluation_qa_trace, '$.performance.output_tokens')) from runs;

# get cost
# select sum(json_extract(trace, '$.performance.cost'))+ sum(json_extract(evaluation_crit_trace, '$.performance.cost'))+ sum(json_extract(evaluation_qa_trace, '$.performance.cost')) from runs;

# 19-Jan run
# Tokens: 488297|65375
# Cost: $6.84

question = 'are pull requests a good practice?'
fill_memory_question = 'what are pull requests?'
true_answer = 'Based on the provided context, it seems that the speaker, Dave Farley, has reservations about the effectiveness of pull requests in software development, especially when it comes to continuous integration. He suggests that pull requests might not be the best practice as they can impede the swift feedback loop essential for continuous integration. Farley appears to advocate for non-blocking code reviews as a more effective alternative, emphasizing the need for frequent evaluation of changes and quick feedback. Therefore, according to this perspective, pull requests might not be considered a good practice in the context of continuous integration and high-quality, efficient code development.'

llm_models = {
  'openai': ['gpt-3.5-turbo-16k'],
  'ollama': ['mistral:latest', 'llama2:latest']
}
qa_chain_types = ['base', 'conversation']
doc_chain_types = ['stuff', 'map_reduce']
search_types = ['similarity', 'similarity_score_threshold', 'mmr']
similarity_score_thresholds = [0.0, 0.25, 0.5]
custom_prompts = [False, True]

eval_criteria = [ 'helpfullness', 'comprehensiveness', 'relevance to software engineering' ]
eval_models = {
  'gpt-3.5-turbo-16k': 'llama2:13b',
  'mistral:latest': 'llama2:latest',
  'llama2:latest': 'mistral:latest',
  'llama2:13b': 'llama2:13b',
  'llama2:70b': 'llama2:13b'
}

def main():

  for llm in llm_models.keys():
    for model in llm_models[llm]:
      for qa_chain_type in qa_chain_types:
        for doc_chain_type in doc_chain_types:
          for search_type in search_types:
            thresholds = similarity_score_thresholds if search_type == 'similarity_score_threshold' else [0]
            for similarity_score_threshold in thresholds:
              for custom_prompt in custom_prompts:
                
                print(f'llm: {llm}, model: {model}, qa_chain_type: {qa_chain_type}, doc_chain_type: {doc_chain_type}, search_type: {search_type}, similarity_score_threshold: {similarity_score_threshold}, custom_prompt: {custom_prompt}')  

                # for conversation reset and fill memory
                if qa_chain_type == 'conversation':
                  res = requests.get(f'http://localhost:5555/reset').json()
                  res = requests.get(f'http://localhost:5555/ask?question={fill_memory_question}').json()

                # now ask
                url = f'http://localhost:5555/ask?question={question}&llm={llm}&openai_model={model}&ollama_model={model}&chain_type={qa_chain_type}&doc_chain_type={doc_chain_type}&search_type={search_type}&score_threshold={similarity_score_threshold}&custom_prompts={custom_prompt}'
                res = requests.get(url).json()

                # now eval
                id = res['chain']['id']
                eval_model = eval_models[model]
                print(f'evaluating {model} with {eval_models[model]}')
                url=f'http://localhost:5555/evaluate/criteria?id={id}&criteria={",".join(eval_criteria)}&llm=ollama&ollama_model={eval_model}'
                requests.get(url).json()
                url=f'http://localhost:5555/evaluate/qa?id={id}&reference={true_answer}&llm=ollama&ollama_model={eval_model}'
                requests.get(url).json()

if __name__ == '__main__':
  main()