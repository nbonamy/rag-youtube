
// init vue
var vm = new Vue({
  el: '#app',
  data: {
    configuration: {},
    models: [],
    channel: null,
    question: null,
    messages: [ ],
    response: null,
    jsonCode: null,
    historyIndex: 0,
    isLoading: false,
    configuring: false,
  },
  computed: {
    has_question() {
      return this.question != null && this.question.trim().length > 0
    },
    performance() {
      let perf = this.response?.performance
      return `Total time: ${perf?.total_time} ms / Tokens: ${perf?.tokens} / Time to 1st token: ${perf?.time_1st_token} ms / Tokens per sec: ${perf?.tokens_per_sec}`
    }
  },
  methods: {
    onkey(event) {
      if (event.keyCode == 38 || event.keyCode == 40) {
        let maxIndex = this.messages.length / 2
        this.historyIndex = Math.max(0, Math.min(maxIndex, this.historyIndex + (39 - event.keyCode)))
        if (this.historyIndex == 0) {
          this.question = null
        } else {
          this.question = this.messages[this.messages.length - 2 * this.historyIndex].text
        }
      } else if (event.keyCode == 13) {
        this.ask()
      }
    },
    reset() {
      this.isLoading = true
      axios.get('/reset').then(response => {
        this.messages = [ ]
        this.response = null
        this.isLoading = false
        this.historyIndex = 0
      }).catch(_ => {
        this.isLoading = false
        this.showError('Error while resetting model.')
      })
    },
    ask() {
      this.isLoading = true
      this.historyIndex = 0
      this.messages.push({ role: 'user', 'text': this.question })
      this.scrollDiscussion()
      parameters = Object.entries(this.configuration).map(([key, value]) => `${key}=${value}`).join('&')
      axios.get(`/ask?question=${this.question}&${parameters}`).then(response => {
        this.question = null
        this.response = response.data
        this.messages.push({ role: 'assistant', 'text': this.response.text, 'response': this.response })
        this.scrollDiscussion()
        this.isLoading = false
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
    showJson(json) {
      this.jsonCode = JSON.stringify(json, null, 2)//.replace(/\\n/g, '\n')
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
