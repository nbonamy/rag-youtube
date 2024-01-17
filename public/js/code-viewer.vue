<template>
  <div class="modal-card" style="width: 800px; margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">{{ title }}</p></header>
    <section class="modal-card-body">
      <pre>{{ code }}</pre>
    </section>
    <footer class="modal-card-foot">
      <b-button label="Close" @click="$parent.close()" />
    </footer>
  </div>
</template>

<script>
export default {
  props: [ 'code', 'title' ],
}
</script>

<style scoped>

pre {
	white-space: pre-wrap;
}

</style>