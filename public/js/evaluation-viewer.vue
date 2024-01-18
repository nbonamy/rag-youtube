<template>
  <div class="modal-card" style="margin: 0 auto;">
    <header class="modal-card-head"><p class="modal-card-title">Evaluation</p></header>
    <section class="modal-card-body">
      <table class="evaluation">
        <tr v-for="(rating, criteria) in evaluation" :key="criteria">
          <th class="criteria">{{ criteria }}</th>
          <td class="rating">
            <b-rate :value="rating" :disabled="true" :show-score="true" :spaced="true"></b-rate>
          </td>
        </tr>
      </table>
    </section>
    <footer class="modal-card-foot">
      <b-button label="Close" @click="$parent.close()"></b-button>
    </footer>
  </div>
</template>

<script>
export default {
  props: [ 'evaluation' ],
  show: function(vue, evaluation) {
    if (Object.keys(evaluation).length > 0) {
      vue.$buefy.modal.open({
        parent: vue,
        trapFocus: true,
        hasModalCard: true,
        component: EvaluationViewer,
        props: {
          evaluation: evaluation,
        }
      })
    } else {
      vue.$buefy.dialog.alert({
        title: 'Answer Evaluation',
        message: evaluation.replace('\n', '<br>'),
      })
    }
  }
}
</script>

<style scoped>

.evaluation th, .evaluation td {
	padding: 2px 8px;
}

.evaluation .criteria {
	text-align: right;
}

</style>