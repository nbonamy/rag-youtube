<template>
  <div class="chain">
    <step :step="chain.chain" :level="0"></step>
    <div class="step chain">
      <div class="header">
        <div>{{ performance }}</div>
        <div>
          Total input tokens: {{ chain.performance.input_tokens }} /
          Total output tokens: {{ chain.performance.output_tokens }} /
          Estimated cost: ${{ chain.performance.cost.toFixed(3) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  components: { 'step': Step, },
  props: [ 'chain' ],
  computed: {
    performance() {
      return formatPerformance(this.chain.performance, OUTPUT_TOKENS_ONLY)
    }
  }
}
</script>
