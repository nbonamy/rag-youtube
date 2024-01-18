<template>
  <div class="modal-card" style="margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">{{ title }}</p></header>
    <section class="modal-card-body">
      <b-input v-model="value" type="textarea"></b-input>
    </section>
    <footer class="modal-card-foot">
      <b-button type="is-info" label="OK" @click="$parent.close(); callback(value)"></b-button>
      <b-button label="Close" @click="$parent.close()" />
    </footer>
  </div>
</template>

<script>

export default {
  props: [ 'title', 'initialValue', 'callback' ],
  data: function() {
    return { value: this.initialValue ?? '' }
  },
  prompt: function(vue, title, callback) {
    vue.$buefy.modal.open({
      parent: vue,
      trapFocus: true,
      hasModalCard: true,
      component: Prompt,
      props: {
        title: title,
        callback: callback,
      }
    })
  }
}
</script>
