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

<style>

/* this is not scoped as it is used by the chain component */

.step {
	margin-top: 8px;
	margin-bottom: 8px;
	font-size: 13px;
}

.step .header {
	border: 1px solid black;
	border-radius: 4px;
	padding: 8px;
	cursor: pointer;
	color: #202020;
}

/* from https://creativemarket.com/FemDemirsoy/10222090-Color-Palette-Procreate-Illustrator */

.step.chain .header {
	background-color: rgba(140,64,52,5%);
	border-color: rgba(140,64,52,50%);
}

.step.llm .header {
	background-color: rgba(66,142,199,5%);
	border-color: rgba(66,142,199,50%);
}

.step.retriever .header {
	background-color: rgba(78,103,92,5%);
	border-color: rgba(78,103,92,50%);
}

.step .header .performance {
	float: right;
	text-align: right;
	margin-left: 8px;
	font-style: italic;
}

.step .header .title {
	font-size: 14px;
	font-weight: bold;
	margin-bottom: 0;
}

.step.chain .header .title {
	color: rgba(140,64,52,100%);
}

.step.llm .header .title {
	color: rgba(66,142,199,100%);	
}

.step.retriever .header .title {
	color: rgba(78,103,92,100%);
}

.step .header * {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

</style>