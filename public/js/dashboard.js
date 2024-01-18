
// init vue
var vm = new Vue({
  el: '#app',
  data: () => {
    return {
      isLoading: false,
      channel: null,
      runs: [],
    }
  },
  computed: {
  },
  methods: {
    timeClass(time) {
      if (time > 10000) return 'is-danger'
      else if (time > 5000) return 'is-warning'
      else return 'is-success'
    },
    showQA(run) {
      ObjectViewer.show(this, 'Question/Answer', {
        'question': run.trace.question,
        'answer': run.trace.answer
      })
    },
    showCode(run) {
      CodeViewer.show(this, 'Chain', run.trace)
    },
    showChain(run) {
      let chain = run.trace
      chain.chain.prompt = chain.question
      chain.chain.response = chain.answer
      ChainViewer.show(this, chain)
    },
    deleteRun(run) {
      this.$buefy.dialog.confirm({
        title: 'Deleting run',
        message: `Are you sure you want to delete run ${run.id}?`,
        confirmText: 'Delete',
        type: 'is-danger',
        hasIcon: true,
        onConfirm: () => {
          axios.delete(`/runs/${run.id}`).then(response => {
            this.runs = this.runs.filter(r => r.id != run.id)
          }).catch(_ => {
            this.showError('Error while deleting run.')
          })
        }
      })
    }
  },
  mounted() {

    // load local data
    let localHistory = localStorage.getItem('history')
    if (localHistory) {
      this.history = JSON.parse(localHistory)
    }

    // load remote data
    axios.get('/info').then(response => {
      this.channel = response.data
    }).catch(_ => {
      this.showError('Error while getting channel.')
    })
    axios.get('/runs').then(response => {
      this.runs = response.data.runs.map(run => {
        d = new Date(0)
        d.setUTCSeconds(run.created_at/1000)
        return {
          ...run,
          'date': d.toLocaleString(),
          'type': `${run.type} / ${run.trace.parameters.chain_type} / ${run.trace.parameters.doc_chain_type}`,
          'total_tokens': run.input_tokens + run.output_tokens,
        }
      })
    }).catch(_ => {
      this.showError('Error while getting runs.')
    })
  },
})
