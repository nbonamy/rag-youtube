<template>
  <div class="modal-card" style="width: 800px; margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">{{ title }}</p></header>
    <section class="modal-card-body">
      <pre>{{ formattedCode }}</pre>
    </section>
    <footer class="modal-card-foot">
      <b-button label="Close" @click="$parent.close()"></b-button>
      <b-button label="Prompt" @click="showPrompt()" v-if="hasPrompt"></b-button>
      <b-button label="Response" @click="showResponse()" v-if="hasResponse"></b-button>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'CodeViewer',
  props: [ 'code', 'title', 'asText' ],
  computed: {
    formattedCode() {
      let formatted = JSON.stringify(this.code, null, 2)
      if (this.asText) {
        formatted = formatted.replace(/\\n/g, '\n')
        formatted = formatted.slice(1, -1).trim()
      }
      return formatted
    },
    hasPrompt() {
      let prompt = this.code['prompt'] ?? this.code['question']
      return prompt != null && prompt.length > 0
    },
    hasResponse() {
      let response = this.code['response'] ?? this.code['answer']
      return response != null && response.length > 0
    }
  },
  methods: {
    showPrompt() {
      this.showAsText('Prompt', this.code['prompt'] ?? this.code['question'])
    },
    showResponse() {
      this.showAsText('Response', this.code['response'] ?? this.code['answer'])
    },
    showAsText(title, str) {
      CodeViewer.show(this, title, str, true)
    }
  },
  show: function(vue, title, code, asText=false) {
    vue.$buefy.modal.open({
      parent: vue,
      trapFocus: true,
      hasModalCard: true,
      component: CodeViewer,
      props: {
        title: title,
        code: code,
        asText: asText,
      },
    })
  }
}
</script>

<style scoped>

pre {
	white-space: pre-wrap;
}

</style>