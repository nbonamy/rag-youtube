
// helper
const ALL_TOKENS = 0
const INPUT_TOKENS_ONLY = 1
const OUTPUT_TOKENS_ONLY = 2
const formatPerformance = function(performance, which_tokens=ALL_TOKENS) {
  let tokens = 0
  let label = 'Tokens'
  if (which_tokens == ALL_TOKENS) tokens = performance.input_tokens + performance.output_tokens
  else if (which_tokens == INPUT_TOKENS_ONLY) { tokens = performance.input_tokens; label = 'Input tokens' }
  else if (which_tokens == OUTPUT_TOKENS_ONLY) { tokens = performance.output_tokens; label = 'Output tokens' }
  return `Total time: ${performance?.total_time} ms / ${label}: ${tokens} / Time to 1st token: ${performance?.time_1st_token} ms / Tokens per sec: ${performance?.tokens_per_sec}`
}

// vue sfc loader
const { loadModule } = window['vue2-sfc-loader']
const options = {
  moduleCache: {
    vue: Vue,
  },
  async getFile(url) {
    const res = await fetch(url);
    if ( !res.ok ) throw Object.assign(new Error(res.statusText + ' ' + url), { res })
    else  return { getContentData: (asBinary) => asBinary ? res.arrayBuffer() : res.text(), }
  },
  addStyle(textContent) {
    const style = Object.assign(document.createElement('style'), { textContent })
    const ref = document.head.getElementsByTagName('style')[0] || null
    document.head.insertBefore(style, ref);    
  }
}

async function loadModules() {
  Prompt = await loadModule('./js/prompt.vue', options)
  Configuration = await loadModule('./js/configuration.vue', options)
  CodeViewer = await loadModule('./js/code-viewer.vue', options)
  ObjectViewer = await loadModule('./js/object-viewer.vue', options)
  Step = await loadModule('./js/step.vue', options)
  Chain = await loadModule('./js/chain.vue', options)
  ChainViewer = await loadModule('./js/chain-viewer.vue', options)
  EvaluationViewer = await loadModule('./js/evaluation-viewer.vue', options)
}

loadModules()

const defaultEvalCriteria = [
  'helpful',
  'detailed',
  'relevant to software engineering',
]
