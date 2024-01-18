<template>
  <div class="modal-card" style="width: 800px; margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">{{ title }}</p></header>
    <section class="modal-card-body">
      <div v-for="key in keys" :key="key" class="attribute">
        <div class="key">{{  key }}</div>
        <div class="value" :class="{ 'pre': isCode(obj[key])}">{{ isCode(obj[key]) ? JSON.stringify(obj[key], null, 2) : obj[key] }}</div>
      </div>
    </section>
    <footer class="modal-card-foot">
      <b-button label="Close" @click="$parent.close()"></b-button>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'ObjectViewer',
  props: [ 'title', 'obj' ],
  computed: {
    keys() {
      return Object.keys(this.obj)
    },
  },
  methods: {
    isCode(value) {
      return Array.isArray(value) || typeof value == 'object'
    },
  }
}
</script>

<style scoped>

.attribute {
  border: 1px solid black;
  border-radius: 4px;
  margin-top: 16px;
  margin-bottom: 16px;
}

.attribute * {
  padding: 4px 8px;
  font-size: 10.5pt;
}

.attribute .key {
  font-weight: bold;
  border-bottom: 1px solid black;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  background-color: #eee;
}

.attribute .value.pre {
  white-space: pre-wrap;
}

</style>
