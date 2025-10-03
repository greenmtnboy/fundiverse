<template>
  <div class="query-container">
    <div v-if="loadingDatabase" class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ loadingMessage }}</div>
    </div>
    <div v-else-if="loadError" class="error-state">
      <div class="error-icon">⚠️</div>
      <div class="error-text">{{ loadError }}</div>
      <button @click="retryLoad" class="retry-button">Retry</button>
    </div>
    <div v-else-if="loaded" class="data-display">
      <vega-lite-chart :data="editorStore.editors[editorId].results.data"
        :columns="editorStore.editors[editorId].results.headers" />
    </div>
    <div v-else>
      Initializing...
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
import { ModelConfig, ModelSource } from 'trilogy-studio-components/models'
import instance from '/src/api/instance'
import type { Import } from 'trilogy-studio-components/stores/resolver.ts'
export default {
  name: 'PortfoloioAnalytics',
  components: {
    ResultComponent,
    VegaLiteChart
  },
  props: {
    portfolioName: {
      type: String,
      required: true
    },
  },
  setup(props) {
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
    let loadingDatabase = ref(false)
    let loadingMessage = ref('')
    let loadError = ref('')
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
    const loadTrilogyModels = async () => {

      loadingMessage.value = 'Loading Trilogy models...'

      // Fetch the trilogy model files
      const response = await instance.get('trilogy_model')
      const files: Record<string, string> = response.data
      const modelName = 'portfolio'
      // check if it's in modelStore.models, create if not
      let modelConfig = modelStore.models[modelName]
      if (!modelConfig) {
        modelStore.newModelConfig(modelName)
      }
      modelConfig = modelStore.models[modelName]
      // Create an editor for each file
      Object.entries(files).forEach(([filename, content]) => {
        const editorName = filename
        let editor = editorStore.getEditorByName(editorName)
        console.log('Creating editor for file:', filename)
        if (!editor) {
          editor = editorStore.newEditor(editorName, 'trilogy', connectionId, content)
        } else {
          // Update content if editor already exists
          editor.text = content
        }

        editor.loading = false
        editor.setError(null)
        modelStore.addModelConfigSource(modelName, new ModelSource(
          editor.id,
          editor.name,
          [],
          []
        ))
      })

      loadingMessage.value = 'Trilogy models loaded successfully!'
      return modelName
    }


    const loadDatabase = async () => {
      loadingDatabase.value = true
      loadError.value = ''
      loadingMessage.value = 'Downloading portfolio database...'

      await connection.connect()

      let model = await loadTrilogyModels()

      connection.setModel(model)

      try {
        // Fetch the database file from the API
        const response = await instance.get(`database/download/${props.portfolioName}`, {
          responseType: 'blob',
          onDownloadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              loadingMessage.value = `Downloading database... ${percentCompleted}%`
            }
          }
        })

        // Convert blob to File object
        const dbFile = new File(
          [response.data],
          `${props.portfolioName}.db`,
          { type: 'application/octet-stream' }
        )

        loadingMessage.value = 'Mounting database to DuckDB...'

        // Import the database file into DuckDB connection
        const onProgress = (message: string) => {
          loadingMessage.value = message
        }

        await connection.importFile(dbFile, onProgress)

        loadingMessage.value = 'Database loaded successfully!'

        // Small delay to show success message
        await new Promise(resolve => setTimeout(resolve, 500))

        loadingDatabase.value = false

        // Now run the query
        await runQuery()

      } catch (err: any) {
        console.error('Database loading failed:', err)
        loadError.value = err.response?.data?.detail || err.message || 'Failed to load portfolio database'
        loadingDatabase.value = false
      }
    }

    const runQuery = async () => {
      let editor = editorStore.getEditorByName(editorName)
      let content = 'SELECT sum(holdings.value) as total_holding_value;'
      if (!editor) {
        editor = editorStore.newEditor(editorName, 'sql', connectionId, content)
      }
      editorId.value = editor.id
      editor.loading = true
      editor.setError(null)

      try {
        // Prepare query input
        const queryInput = {
          text: editor.text,
          editorType: 'preql' as const,
          imports: [{
            name: 'entrypoint',
            alias: ''
          }
          ]
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

    const retryLoad = () => {
      loadError.value = ''
      loadDatabase()
    }

    onMounted(() => {
      loadDatabase()
    })

    return {
      editorStore,
      editorId,
      loaded,
      loadingDatabase,
      loadingMessage,
      loadError,
      retryLoad,
    }
  }
}
</script>

<style scoped>
.query-container {
  padding: 20px;
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 16px;
  color: #666;
  text-align: center;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 30px;
  background-color: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 8px;
}

.error-icon {
  font-size: 48px;
}

.error-text {
  color: #c53030;
  font-size: 16px;
  text-align: center;
  max-width: 400px;
}

.retry-button {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: #2980b9;
}

.data-display {
  margin-top: 20px;
  height: 500px;
  width: 100%;
}
</style>