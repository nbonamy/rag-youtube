#!/usr/bin/env python3

import json
import utils
import consts
from database import Database
from agent_qa import AgentQA
from agent_eval import Evaluator
from config import Config
from bottle import Bottle, request, static_file
from chain_base import ChainParameters

# we need this as a global so we can use it in the ask endpoint
summarizer = None

# and an app with a config
app = Bottle()
app.config.update({
  'config': Config(consts.CONFIG_PATH)
})

agent = AgentQA(app.config.get('config'))
evaluator = Evaluator(app.config.get('config'))
database = Database(app.config.get('config'))

@app.route('/config')
def config():
  config = app.config.get('config')
  return { 'configuration': config.to_dict() }

@app.route('/models/ollama')
def ollama_models():
  return agent.list_ollama_models()

@app.route('/models/openai')
def openai_models():
  return agent.list_openai_models()

@app.route('/info')
def info():
  return static_file('channel_info.json', root='./')

@app.route('/embed')
def embed():
  text = request.query.text
  embeddings = agent.calculate_embeddings(text)
  return { 'text': text, 'length': len(embeddings), 'embeddings': [float(a) for a in embeddings] }

@app.route('/similarity')
def embed():
  text1 = request.query.text1
  text2 = request.query.text2
  similarity = agent.calculate_similarity(text1, text2)
  return { 'text1': text1, 'text2': text2, 'similarity': float(similarity[0]) }

@app.route('/reset')
def reset():
  agent.reset()
  return { 'status': 'ok' }

@app.route('/cost')
def cost():
  input_tokens = request.query.input_tokens
  output_tokens = request.query.output_tokens
  return { 'cost': utils.cost(input_tokens, output_tokens) }

@app.route('/ask')
def ask():

  # with open('response.json', 'r') as f:
  #   return json.loads(f.read())
  
  # do it
  question = request.query.question
  overrides = {k:v[0] for k,v in request.query.dict.items()}
  result = agent.query(question, overrides)
  
  # done
  return result

@app.route('/evaluate/<method>')
def eval(method):

  # get data
  run_id = request.query.id
  answer = request.query.answer
  overrides = {k:v[0] for k,v in request.query.dict.items()}

  # do it
  if method == 'criteria':
    criteria = request.query.criteria.split(',')
    result = evaluator.evaluate_criteria(run_id, answer, criteria, overrides)
  elif method == 'qa':
    question = request.query.question
    reference = request.query.reference
    result = evaluator.evaluate_qa(run_id, question, answer, reference, overrides)
  else:
    raise Exception(f'Unknown evaluation method {method}')

  # done
  return result

@app.route('/runs')
def get_runs():
  return { 'runs': database.get_runs() }

@app.delete('/runs/<id>')
def delete_run(id):
  database.delete_run(id)
  return { 'status': 'ok' }

@app.route('/<filepath:path>')
def server_static(filepath):
  return static_file(filepath, root='./public')  

@app.route('/')
def server_index():
  return static_file('index.html', root='./public')

# run server
app.run(host='0.0.0.0', port=5555, debug=True)
