#!/usr/bin/env python3

import json
import consts
from agent import Agent
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

agent = Agent(app.config.get('config'))

@app.route('/config')
def config():
  config = app.config.get('config')
  parameters = ChainParameters(config, {})
  return {
    'configuration': parameters.to_dict() | {
      'ollama_model': config.ollama_model()
    }
  }

@app.route('/models')
def models():
  return agent.list_ollama_models()

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

@app.route('/eval')
def eval():

  # do it
  text = request.query.text
  criteria = request.query.criteria.split(',')
  overrides = {k:v[0] for k,v in request.query.dict.items()}
  result = agent.evaluate(text, criteria, overrides)

  # done
  return result

@app.route('/<filepath:path>')
def server_static(filepath):
  return static_file(filepath, root='./public')  

@app.route('/')
def server_index():
  return static_file('index.html', root='./public')

# run server
app.run(host='0.0.0.0', port=5555, debug=True)
