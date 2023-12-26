#!/usr/bin/env python3

import utils
import consts
import os.path
from agent import Agent
from config import Config
from bottle import Bottle, request, abort, static_file

# we need this as a global so we can use it in the ask endpoint
summarizer = None

# and an app with a config
app = Bottle()
app.config.update({
  'config': Config(consts.CONFIG_PATH)
})

agent = Agent(app.config.get('config'))

@app.route('/info')
def info():
  print('hello')
  return static_file('channel_info.json', root='./')

@app.route('/embed')
def embed():
  text = request.query.text
  embeddings = agent.calculate_embeddings(text)
  return { 'text': text, 'length': len(embeddings), 'embeddings': [float(a) for a in embeddings] }

@app.route('/ask')
def ask():

  # do it
  question = request.query.question
  start = utils.now()
  result = agent.query(question)
  processing_time = utils.now() - start
  
  # done
  result['performance']['processing_time'] = int(processing_time)
  result['performance']['total_time'] = int(processing_time)
  return result

@app.route('/<filepath:path>')
def server_static(filepath):
  return static_file(filepath, root='./public')  

@app.route('/')
def server_index():
  return static_file('index.html', root='./public')

# run server
app.run(host='0.0.0.0', port=5555, debug=True)
