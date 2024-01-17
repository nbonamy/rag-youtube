<template>
  <form action="">
    <div class="modal-card" style="width: 600px; margin: 0 auto;">
      <header class="modal-card-head"><p class="modal-card-title">Configuration</p></header>
      <section class="modal-card-body">
        <b-field label="Ollama Model">
          <b-select v-model="configuration.ollama_model" :expanded="true">
            <option v-for="model in models"
              :value="model.name"
              :key="model.digest">
              {{ model.name }}
            </option>
          </b-select>
        </b-field>
        <b-field label="QA Chain Type">
          <b-select v-model="configuration.chain_type" :expanded="true">
            <option value="base">Basic</option>
            <option value="sources">Sourced</option>
            <option value="conversation">Conversational</option>
          </b-select>
        </b-field>
        <b-field label="Doc Chain Type">
          <b-select v-model="configuration.doc_chain_type" :expanded="true">
            <option value="stuff">Stuff</option>
            <option value="map_reduce">MapReduce</option>
          </b-select>
        </b-field>
        <b-field label="Search Type">
          <b-select v-model="configuration.search_type" :expanded="true">
            <option value="similarity">Similarity</option>
            <option value="similarity_score_threshold">Score Threshold</option>
            <option value="mmr">MMR</option>
          </b-select>
        </b-field>
        <b-field label="Similarity Threshold">
          <b-input type="number" min="0" max="1" step="0.01" v-model="configuration.score_threshold"></b-input>
        </b-field>
        <b-field label="Documents Count">
          <b-input type="number" v-model="configuration.document_count" min="1"></b-input>
        </b-field>
        <b-field>
          <b-checkbox v-model="configuration.custom_prompts">Use Custom Prompts</b-checkbox>
        </b-field>
        <b-field>
          <b-checkbox v-model="configuration.return_sources">Return Sources</b-checkbox>
        </b-field>
      </section>
      <footer class="modal-card-foot">
        <b-button label="Close" @click="$parent.close()" />
      </footer>
    </div>
  </form>  
</template>

<script>
export default {
  props: [ 'configuration', 'models' ],
}
</script>
