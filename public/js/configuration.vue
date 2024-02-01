<template>
  <form action="">
    <div class="modal-card" style="width: 600px; margin: 0 auto;">
      <header class="modal-card-head"><p class="modal-card-title">Configuration</p></header>
      <section class="modal-card-body">
        <b-field label="LLM" horizontal>
          <b-select v-model="configuration.llm" :expanded="true">
            <option value="ollama">Ollama</option>
            <option value="openai">OpenAI</option>
          </b-select>
        </b-field>
        <b-field label="Ollama Model" horizontal v-if="configuration.llm == 'ollama'">
          <b-select v-model="configuration.ollama_model" :expanded="true">
            <option v-for="model in models.ollama"
              :value="model.name"
              :key="model.name">
              {{ model.name }}
            </option>
          </b-select>
        </b-field>
        <b-field label="OpenAI Model" horizontal v-if="configuration.llm == 'openai'">
          <b-input v-model="configuration.openai_model"></b-input>
        </b-field>
        <b-field label="LLM Temperature" horizontal>
          <b-input type="number" min="0" max="1" step="0.05" v-model="configuration.llm_temperature"></b-input>
        </b-field>
        <b-field label="QA Chain Type" horizontal>
          <b-select v-model="configuration.chain_type" :expanded="true">
            <option value="base">Basic</option>
            <option value="sources">Sourced</option>
            <option value="conversation">Conversational</option>
          </b-select>
        </b-field>
        <b-field label="Doc Chain Type" horizontal>
          <b-select v-model="configuration.doc_chain_type" :expanded="true">
            <option value="stuff">Stuff</option>
            <option value="map_reduce">MapReduce</option>
            <option value="refine">Refine</option>
            <option value="map_rerank">MapRerank</option>
          </b-select>
        </b-field>
        <b-field label="Retriever Type" horizontal>
          <b-select v-model="configuration.retriever_type" :expanded="true">
            <option value="base">Standard</option>
            <option value="multi_query">Multi-Query</option>
            <option value="compressor">Contextual Compression</option>
          </b-select>
        </b-field>
        <b-field label="Search Type" horizontal>
          <b-select v-model="configuration.search_type" :expanded="true">
            <option value="similarity">Similarity</option>
            <option value="similarity_score_threshold">Score Threshold</option>
            <option value="mmr">MMR</option>
          </b-select>
        </b-field>
        <b-field label="Similarity Threshold" horizontal>
          <b-input type="number" min="0" max="1" step="0.05" v-model="configuration.score_threshold"></b-input>
        </b-field>
        <b-field label="Documents Count" horizontal>
          <b-input type="number" v-model="configuration.document_count" min="1"></b-input>
        </b-field>
        <b-field label="" horizontal>
          <b-checkbox v-model="configuration.custom_prompts">Use Custom Prompts</b-checkbox>
        </b-field>
        <b-field label="" horizontal>
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
  show: function(vue, models, configuration) {
    vue.$buefy.modal.open({
      parent: vue,
      trapFocus: true,
      hasModalCard: true,
      component: Configuration,
      props: {
        models: models,
        configuration: configuration
      },
    })
  }
}
</script>

<style>
.field-label {
  white-space: nowrap;
  flex-basis: 100px;
}
</style>