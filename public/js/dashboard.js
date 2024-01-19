
// init vue
var vm = new Vue({
  el: '#app',
  data: () => {
    return {
      isLoading: false,
      channel: null,
      runs: [],
      evalCriteria: defaultEvalCriteria,
    }
  },
  computed: {
  },
  methods: {
    loadRuns() {
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
    timeClass(time) {
      if (time > 10000) return 'is-danger'
      else if (time > 5000) return 'is-warning'
      else return 'is-success'
    },
    evalCritClass(run) {
      let eval_crit = this.getEvalCrit(run)
      if (eval_crit >= 4) return 'is-success'
      else if (eval_crit <= 2) return 'is-danger'
      else return ''
    },
    evalQAClass(run) {
      let eval_qa = this.getEvalQA(run)
      if (eval_qa == 'CORRECT') return 'is-success'
      else if (eval_qa == 'INCORRECT') return 'is-danger'
      else return ''
    },
    showQA(run) {
      ObjectViewer.show(this, 'Question/Answer', {
        'question': run.trace.question,
        'answer': run.trace.answer
      })
    },
    showCode(trace) {
      CodeViewer.show(this, 'Chain', trace)
    },
    showChain(trace) {
      let chain = trace
      chain.chain.prompt = chain.question
      chain.chain.response = chain.answer
      ChainViewer.show(this, chain)
    },
    showEvalCrit(trace) {
      EvaluationViewer.show(this, trace.evaluation)
    },
    showEvalQa(trace) {
      CodeViewer.show(this, 'Evaluation', trace.answer, true)
    },
    getEvalCrit(run) {
      if (run.evaluation_crit_trace == null) return 'N/A'
      let evaluation = run.evaluation_crit_trace.evaluation
      let keys = Object.keys(evaluation)
      if (keys.length == 0) return 'N/A'
      let total = keys.reduce((acc, key) => acc + evaluation[key], 0)
      return (total / keys.length).toFixed(1)
    },
    getEvalQA(run) {
      if (run.evaluation_qa_trace == null) return 'N/A'
      let eval_qa = run.evaluation_qa_trace.answer
      if (eval_qa == null) return 'N/A'
      if (eval_qa.indexOf('INCORRECT') >= 0) return 'INCORRECT'
      if (eval_qa.indexOf('CORRECT') >= 0) return 'CORRECT'
      return 'N/A'
    },
    runEvalCrit(run) {
      this.isLoading = true
      axios.get(`/evaluate/criteria?id=${run.id}&criteria=${this.evalCriteria.join(",")}`).then(_ => {
        this.loadRuns()
        this.isLoading = false
      }).catch(_ => {
        this.showError('Error while evaluating answer.')
      })
    },
    runEvalQA(run) {
      Prompt.prompt(this, 'Enter reference text', (value) => {
        this.isLoading = true
        axios.get(`/evaluate/qa?id=${run.id}&reference=${value}`).then(_ => {
          this.loadRuns()
          this.isLoading = false
        }).catch(_ => {
          this.showError('Error while comparing answer.')
        })
      })
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
    this.loadRuns()
    axios.get('/info').then(response => {
      this.channel = response.data
    }).catch(_ => {
      this.showError('Error while getting channel.')
    })
  },
})
