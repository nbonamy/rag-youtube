
// init vue
var vm = new Vue({
  el: '#app',
  data: {
    channel: null,
    question: null,
    messages: [ ],
    response: null,
    jsonCode: null,
    isLoading: false,
  },
  computed: {
    performance() {
      let perf = this.response?.performance
      return `Total time: ${perf?.total_time} ms / Tokens: ${perf?.tokens} / Time to 1st token: ${perf?.time_1st_token} ms / Tokens per sec: ${perf?.tokens_per_sec}`
    }
  },
  methods: {
    onkey(event) {
      if (event.keyCode == 13) {
        this.ask()
      }
    },
    reset() {
      this.isLoading = true
      axios.get('/reset').then(response => {
        this.messages = [ ]
        this.response = null
        this.isLoading = false
      }).catch(_ => {
        this.isLoading = false
        this.showError('Error while resetting model.')
      })
    },
    ask() {
      this.isLoading = true
      this.messages.push({ role: 'user', 'text': this.question })
      this.scrollDiscussion()
      axios.get(`/ask?question=${this.question}`).then(response => {
        this.question = null
        this.response = response.data
        this.messages.push({ role: 'assistant', 'text': this.response.text, 'response': this.response })
        this.scrollDiscussion()
        this.isLoading = false
      }).catch(_ => {
        this.showError('Error while asking model.')
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
    axios.get('/info').then(response => {
      this.channel = response.data
    }).catch(_ => {
      this.showError('Error while getting channel.')
    })
  },
})
