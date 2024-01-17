<template>
  <div class="step" :class="step.type" :style="{ 'margin-left': (level==0?0:16) + 'px' }" :data-level="level">
    <div class="header" @click="showCode()">
      <div class="performance">
        <div>{{ step.elapsed }} ms</div>
        <div v-if="step.type == 'llm'">
          <div>{{ step.input_tokens }} tok(s)</div>
          <div>{{ step.output_tokens }} tok(s)</div>
        </div>
      </div>
      <div class="title">{{ title }}</div>
      <div v-if="level == 0">
        <div class="prompt">{{ step.prompt }}</div>
        <div class="response">{{ step.response }}</div>
      </div>
      <div v-if="step.type == 'retriever'">
        <div class="prompt">{{ step.query }}</div>
        <div class="sources">{{ sources.join(', ') }}</div>
      </div>
      <div v-if="step.type == 'llm'">
        <div class="prompt">{{ step.prompt }}</div>
        <div class="response">{{ step.response ?? '[N/A]' }}</div>
      </div>
    </div>
    <step :step="step" :level="level+1" :key="step.id" v-for="step in step.steps"></step>
  </div>
</template>

<script>
export default {
  name: 'Step',
  props: [ 'step', 'level' ],
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
    showCode() {
      let clone = JSON.parse(JSON.stringify(this.step))
      delete clone.steps
      this.code = JSON.stringify(clone, null, 2)
      this.$buefy.modal.open({
        parent: this,
        trapFocus: true,
        hasModalCard: true,
        component: CodeViewer,
        props: {
          title: this.title,
          code: JSON.stringify(clone, null, 2),
        },
      })
    },
  }
}
</script>