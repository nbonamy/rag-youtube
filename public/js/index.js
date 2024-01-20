
// init vue
var vm = new Vue({
  el: '#app',
  data: () => {
    return {
      configuration: {},
      models: {
        'ollama': [],
        'openai': [],
      },
      channel: null,
      question: null,
      messages: [],
      history: [],
      historyIndex: 0,
      response: null,
      isLoading: false,
      evalCriteria: defaultEvalCriteria,
    }
  },
  computed: {
    has_question() {
      return this.question != null && this.question.trim().length > 0
    },
    performance() {
      return formatPerformance(this.response?.performance, OUTPUT_TOKENS_ONLY)
    },
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
        this.showError('Error while resetting model.')
      })
    },
    editConfiguration() {
      Configuration.show(this, this.models, this.configuration)
    },
    requestOverrides() {
      return Object.entries(this.configuration).map(([key, value]) => `${key}=${value}`).join('&')
    },
    ask() {
      this.isLoading = true
      this.historyIndex = 0
      this.messages.push({ role: 'user', 'text': this.question })
      this.scrollDiscussion()
      axios.get(`/ask?question=${this.question}&${this.requestOverrides()}`).then(response => {
        this.response = response.data
        this.messages.push({ role: 'assistant', 'text': this.response.answer, 'response': this.response })
        this.addHistory(this.question)
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
    showCode(response) {
      CodeViewer.show(this, 'Chain', response)
    },
    showChain(response) {
      let chain = response
      chain.chain.prompt = chain.question
      chain.chain.response = chain.answer
      ChainViewer.show(this, chain)
    },
    evalCrit(response) {
      this.isLoading = true
      this.historyIndex = 0
      this.messages.push({ role: 'user', 'text': `Evaluate the response against ${this.evalCriteria.join(", ")}` })
      this.scrollDiscussion()
      axios.get(`/evaluate/criteria?id=${response.chain.id}&answer=${response.answer}&criteria=${this.evalCriteria.join(",")}&${this.requestOverrides()}`).then(response => {
        this.response = response.data
        this.messages.push({ role: 'evaluator', 'text': this.response.answer, 'response': this.response })
        this.question = null
        this.isLoading = false
        this.scrollDiscussion()
        this.showEvalCrit(response.data)
      }).catch(_ => {
        this.showError('Error while evaluating answer.')
      })
    },
    showEvalCrit(response) {
      EvaluationViewer.show(this, response.evaluation)
    },
    evalQA(response) {
      Prompt.prompt(this, 'Enter reference text', (value) => {
        this.isLoading = true
        this.historyIndex = 0
        this.messages.push({ role: 'user', 'text': 'Evaluate the response' })
        this.scrollDiscussion()
          axios.get(`/evaluate/qa?id=${response.chain.id}&question=${response.question}&answer=${response.answer}&reference=${value}&${this.requestOverrides()}`).then(response => {
          this.response = response.data
          this.messages.push({ role: 'evaluator', 'text': this.response.answer, 'response': this.response })
          this.question = null
          this.isLoading = false
          this.scrollDiscussion()
        }).catch(_ => {
          this.showError('Error while comparing answer.')
        })
      })
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
    },
    addHistory() {
      if (this.history[this.history.length - 1] != this.question) {
        this.history.push(this.question)
        localStorage.setItem('history', JSON.stringify(this.history))
      }
    },
  },
  mounted() {

    // load local data
    let localHistory = localStorage.getItem('history')
    if (localHistory) {
      this.history = JSON.parse(localHistory)
    }

    // load remote data
    axios.get('/config').then(response => {
      this.configuration = response.data.configuration
    }).catch(_ => {
      this.showError('Error while getting configuration.')
    })
    axios.get('/models/ollama').then(response => {
      this.models.ollama = response.data.models
    }).catch(_ => {
      this.showError('Error while getting ollama models information.')
    })
    axios.get('/info').then(response => {
      this.channel = response.data
    }).catch(_ => {
      this.showError('Error while getting channel.')
    })
  },
})
