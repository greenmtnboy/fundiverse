<template>
  <div class="query-container">
    <div v-if="loaded" class="data-display">
      <!-- <result-component :editorData="editorStore.editors[editorId]" :containerHeight="500" /> -->
      <vega-lite-chart :data="editorStore.editors[editorId].results.data"
        :columns="editorStore.editors[editorId].results.headers" />
    </div>
    <div v-else>
      Loading...
    </div>
  </div>
</template>

<script lang="ts">
import { ref, onMounted, inject, provide } from 'vue'
import useEditorStore from 'trilogy-studio-components/stores/editorStore'
import { useConnectionStore, useModelConfigStore } from 'trilogy-studio-components/stores'
import { useUserSettingsStore } from 'trilogy-studio-components/stores'
import ResultComponent from 'trilogy-studio-components/components/editor/ResultComponent.vue'
import VegaLiteChart from 'trilogy-studio-components/components/VegaLiteChart.vue'
import { DuckDBConnection } from 'trilogy-studio-components/connections'
import { QueryExecutionService } from 'trilogy-studio-components/stores'
import { TrilogyResolver } from 'trilogy-studio-components/stores'

export default {
  name: 'SimpleSQLQuery',
  components: {
    ResultComponent,
    VegaLiteChart
  },
  props: {
    portfolioName: String,
  },
  setup() {
    let editorStore = useEditorStore()
    let connectionStore = useConnectionStore()
    let userSettingsStore = useUserSettingsStore()
    let modelStore = useModelConfigStore()

    let resolver = new TrilogyResolver(userSettingsStore)
    let queryExecutionService = new QueryExecutionService(resolver, connectionStore, modelStore, editorStore)
    provide('editorStore', editorStore)
    provide('connectionStore', connectionStore)
    provide('userSettingsStore', userSettingsStore)
    provide('queryExecutionService', queryExecutionService)

    let loaded = ref(false)
    let editorId = ref('')

    const editorName = 'simple-query-editor'
    const connectionId = 'portfolio-query'

    let connection: DuckDBConnection | null = null;

    if (!connectionStore.connections[connectionId]) {
      connection = connectionStore.newConnection(connectionId, 'duckdb', {}) as DuckDBConnection
    }
    else {
      connection = connectionStore.connections[connectionId] as DuckDBConnection
    }


    if (!editorStore) {
      throw new Error('Editor store not provided')
    }



    const runQuery = async () => {


      let editor = editorStore.getEditorByName(editorName)
      if (!editor) {
        editor = editorStore.newEditor(editorName, 'sql', connectionId, '')
      }
      editorId.value = editor.id
      editor.loading = true
      editor.setError(null)

      try {

        // Prepare query input
        const queryInput = {
          text: 'SELECT 1 as test;',
          editorType: 'sql' as const,
          imports: []
        }

        // Define callbacks
        const onProgress = (message: any) => {
          if (message.error) {
            editor.loading = false
            editor.setError(message.message)
          }
          if (message.running) {
            editor.error = null
            editor.loading = true
          }
        }

        const onSuccess = (result: any) => {
          if (result.success && result.results) {
            editorStore.setEditorResults(editorId.value, result.results)
            loaded.value = true
          } else if (result.error) {
            editor.setError(result.error)
          }
          editor.loading = false
        }

        const onError = (error: any) => {
          console.error('Query execution error:', error.message)
          editor.setError(error.message || 'An error occurred during query execution')
          editor.loading = false
        }

        // Execute query
        const { resultPromise } = await queryExecutionService.executeQuery(
          connectionId,
          queryInput,
          () => { }, // starter callback
          onProgress,
          onError,
          onSuccess
        )

        await resultPromise
      } catch (err: any) {
        console.error('Query execution failed:', err)
        editor.setError(err.message)
        editor.loading = false
      }
    }

    onMounted(() => {
      runQuery()
    })

    return {
      editorStore,
      editorId,
      loaded,
    }
  }
}
</script>

<style scoped>
.query-container {
  padding: 20px;
  min-height: 500px;
}

.data-display {
  margin-top: 20px;
  height: 500px;
}
</style>