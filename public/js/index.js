
// init vue
var vm = new Vue({
  el: '#app',
  data: {
    channel: null,
    question: null,
    messages: [ ],
    response: null,
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
    ask() {
      this.isLoading = true
      this.messages.push({ role: 'user', 'text': this.question })
      this.scollDiscussion()
      axios.get(`/ask?question=${this.question}`).then(response => {
        this.question = null
        this.response = response.data
        this.messages.push({ role: 'assistant', 'text': this.response.text, 'sources': this.response.sources })
        this.scollDiscussion()
        this.isLoading = false
      }).catch(_ => {
        this.showError('Error while asking model.')
      })
    },
    scollDiscussion() {
      this.$nextTick(() => {
        let discussion = document.getElementsByClassName('discussion')[0]
        discussion.scrollTop = discussion.scrollHeight
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
