<template>
  <div class="modal-card" style="width: 800px; margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">{{ title }}</p></header>
    <section class="modal-card-body" style="min-height: 600px; max-height: 600px; overflow-y: scroll;">
      <chain :chain="chain" />
    </section>
    <footer class="modal-card-foot">
      <b-button label="Close" @click="$parent.close()"></b-button>
      <span>{{ performance }}</span>
    </footer>
  </div>
</template>

<script>
export default {
  components: { Chain },
  props: [ 'chain' ],
  computed: {
    title() {
      return [
        this.chain.parameters.ollama_model,
        this.chain.parameters.chain_type,
        this.chain.parameters.doc_chain_type,
        this.chain.parameters.search_type,
        this.chain.parameters.custom_prompts ? 'custom' : 'default',
      ].join(' / ')
    },
    performance() {
      return formatPerformance(this.chain.performance, ALL_TOKENS)
    }
  },
  show: function(vue, chain) {
    vue.$buefy.modal.open({
      parent: vue,
      trapFocus: true,
      hasModalCard: true,
      component: ChainViewer,
      props: {
        chain: chain,
      },
    })
  }
}
</script>
