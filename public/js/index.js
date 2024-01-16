
// helper
const formatPerformance = function(performance) {
  return `Total time: ${performance?.total_time} ms / Tokens: ${performance?.tokens} / Time to 1st token: ${performance?.time_1st_token} ms / Tokens per sec: ${performance?.tokens_per_sec}`
}

// components
let Step = {
  name: 'Step',
  template: '#step-template',
  props: [ 'step', 'level' ],
  data: () => {
    return {
      isShowingCode: false,
      code: null,
    }
  },
  computed: {
    title() {
      if (this.step.repr == null) return 'ChainStep'
      if (this.step.type == 'llm') return this.step.repr
      return this.step.repr?.split('(')[0]
    },
    sources() {
      return this.step.documents.map((d) => d.source)
    },
  },
  methods: {
    showCode(obj) {
      let clone = JSON.parse(JSON.stringify(this.step))
      delete clone.steps
      this.code = JSON.stringify(clone, null, 2)
      this.isShowingCode = true
    },
  }
}
let Chain = {
  'name': 'Chain',
  template: '#chain-template',
  components: { 'step': Step, },
  props: [ 'chain' ],
  computed: {
    performance() {
      return formatPerformance(this.chain.performance)
    }
  }
}

// init vue
var vm = new Vue({
  el: '#app',
  components: { Chain },
  data: () => {
    return {
      configuration: {},
      models: [],
      channel: null,
      question: null,
      messages: [],
      history: [],
      historyIndex: 0,
      response: null,
      chain: null,
      evaluation: null,      
      isLoading: false,
      isPrompting: false,
      isConfiguring: false,
      isShowingChain: false,
      isShowingEval: false,
      prompt: {
        'title': 'Enter value',
        'value': '',
        'callback': null,
      },
      eval_criteria: [
        'helpful',
        'detailed',
        'relevant to software engineering',
      ],
    }
  },
  computed: {
    has_question() {
      return this.question != null && this.question.trim().length > 0
    },
    performance() {
      return formatPerformance(this.response?.performance)
    }
  },
  methods: {
    onkey(event) {
      if (event.keyCode == 38 || event.keyCode == 40) {
        this.historyIndex = Math.max(0, Math.min(this.history.length, this.historyIndex + (39 - event.keyCode)))
        if (this.historyIndex == 0) {
          this.question = null
        } else {
          event.preventDefault()
          this.question = this.history[this.history.length - this.historyIndex]
          this.$nextTick(() => {
            let prompt = this.$refs.prompt.getElement()
            prompt.setSelectionRange(prompt.value.length, prompt.value.length);
          })
        }
      } else if (event.keyCode == 13) {
        this.ask()
      }
    },
    reset() {
      this.isLoading = true
      axios.get('/reset').then(response => {
        this.messages = []
        this.response = null
        this.isLoading = false
        this.historyIndex = 0
      }).catch(_ => {
        this.isLoading = false
        this.showError('Error while resetting model.')
      })
    },
    request_overrides() {
      return Object.entries(this.configuration).map(([key, value]) => `${key}=${value}`).join('&')
    },
    ask() {
      this.isLoading = true
      this.historyIndex = 0
      this.messages.push({ role: 'user', 'text': this.question })
      this.scrollDiscussion()
      axios.get(`/ask?question=${this.question}&${this.request_overrides()}`).then(response => {
        this.response = response.data
        this.messages.push({ role: 'assistant', 'text': this.response.answer, 'response': this.response })
        this.history.push(this.question)
        this.question = null
        this.isLoading = false
        this.scrollDiscussion()
      }).catch(_ => {
        this.showError('Error while asking model.')
        this.messages.pop()
      })
    },
    scrollDiscussion() {
      this.$nextTick(() => {
        let discussion = document.getElementsByClassName('discussion')[0]
        discussion.scrollTop = discussion.scrollHeight
      })
    },
    showChain(response) {
      this.chain = response
      this.chain.chain.prompt = this.chain.question
      this.chain.chain.response = this.chain.answer
      this.isShowingChain = true
    },
    evalCrit(response) {
      this.isLoading = true
      this.historyIndex = 0
      this.messages.push({ role: 'user', 'text': `Evaluate the response against ${this.eval_criteria.join(", ")}` })
      this.scrollDiscussion()
      axios.get(`/evaluate/criteria?answer=${response.answer}&criteria=${this.eval_criteria.join(",")}&${this.request_overrides()}`).then(response => {
        this.response = response.data
        this.messages.push({ role: 'evaluator', 'text': this.response.answer, 'response': this.response })
        this.question = null
        this.isLoading = false
        this.scrollDiscussion()
        this.showEvalCrit(response.data)
      }).catch(_ => {
        this.isLoading = false
        this.showError('Error while evaluating answer.')
      })
    },
    showEvalCrit(response) {
      if (Object.keys(response.evaluation).length > 0) {
        this.evaluation = response.evaluation
        this.isShowingEval = true
      } else {
        this.$buefy.dialog.alert({
          title: 'Answer Evaluation',
          message: response.answer.replace('\n', '<br>'),
        })
      }
    },
    evalQA(response) {
      this.prompt.title = 'Enter reference text'
      this.prompt.value = ''
      this.prompt.callback = () => {
        this.isPrompting = false
        this.isLoading = true
        this.historyIndex = 0
        this.messages.push({ role: 'user', 'text': 'Evaluate the response' })
        this.scrollDiscussion()
          axios.get(`/evaluate/qa?question=${response.question}&answer=${response.answer}&reference=${this.prompt.value}&${this.request_overrides()}`).then(response => {
          this.response = response.data
          this.messages.push({ role: 'evaluator', 'text': this.response.answer, 'response': this.response })
          this.question = null
          this.isLoading = false
          this.scrollDiscussion()
        }).catch(_ => {
          this.isLoading = false
          this.showError('Error while comparing answer.')
        })
      }
      this.isPrompting = true
    },
    showError(msg) {
      this.isLoading = false
      this.$buefy.dialog.alert({
        title: 'Error',
        message: msg,
        type: 'is-danger',
        hasIcon: true,
        icon: 'alert-circle',
        iconPack: 'mdi'
      })
    }
  },
  mounted() {
    axios.get('/config').then(response => {
      this.configuration = response.data.configuration
    }).catch(_ => {
      this.showError('Error while getting configuration.')
    })
    axios.get('/models').then(response => {
      this.models = response.data.models
    }).catch(_ => {
      this.showError('Error while getting models information.')
    })
    axios.get('/info').then(response => {
      this.channel = response.data
    }).catch(_ => {
      this.showError('Error while getting channel.')
    })
  },
})
