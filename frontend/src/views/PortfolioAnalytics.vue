<template>
  <div class="query-container">
    <DashboardBase ref="dashboardBase" :key="name" :name="name" :connection-id="connectionId" :is-mobile="true" />
    <div v-if="loadingDatabase" class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ loadingMessage }}</div>
    </div>

    <div v-else-if="loadError" class="error-state">
      <div class="error-icon">⚠️</div>
      <div class="error-title">Failed to Load Portfolio</div>
      <div class="error-text">{{ loadError }}</div>
      <button @click="retryLoad" class="retry-button">
        <span class="retry-icon">↻</span>
        Retry
      </button>
    </div>

    <div v-else-if="loaded && dashboardBase" class="data-display">
      <div class="dashboard-mobile-container">
        <div v-for="item in dashboardItems" :key="item.id" class="chart-section">
          <DashboardChart :dashboardId="dashboardId" :itemId="item.id" :setItemData="dashboardBase.setItemData"
            :getItemData="dashboardBase.getItemData" :editMode="false"
            :getDashboardQueryExecutor="dashboardBase.getDashboardQueryExecutor"
            @dimension-click="dashboardBase.setCrossFilter" @background-click="dashboardBase.unSelect" />
        </div>
      </div>
    </div>

    <div v-else class="initializing-state">
      Initializing...
    </div>
  </div>
</template>

<script lang="ts">
import { ref, onMounted, provide } from 'vue'
import useEditorStore from 'trilogy-studio-components/stores/editorStore'
import { useConnectionStore, useModelConfigStore, useDashboardStore, useUserSettingsStore } from 'trilogy-studio-components/stores'
import ResultComponent from 'trilogy-studio-components/components/editor/ResultComponent.vue'
import VegaLiteChart from 'trilogy-studio-components/components/VegaLiteChart.vue'
import { DuckDBConnection } from 'trilogy-studio-components/connections'
import { QueryExecutionService } from 'trilogy-studio-components/stores'
import { TrilogyResolver } from 'trilogy-studio-components/stores'
import { loadTrilogyModels, loadPortfolioDatabase, executePortfolioQuery } from '../helpers/portfolioAnalytics'
import DashboardBase from 'trilogy-studio-components/components/dashboard/DashboardBase.vue'
import DashboardChart from 'trilogy-studio-components/components/dashboard/DashboardChart.vue'
import { CELL_TYPES } from 'trilogy-studio-components/dashboards/base'
export default {
  name: 'PortfolioAnalytics',
  components: {
    ResultComponent,
    VegaLiteChart,
    DashboardBase,
    DashboardChart,
  },
  props: {
    portfolioName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const editorStore = useEditorStore()
    const connectionStore = useConnectionStore()
    const userSettingsStore = useUserSettingsStore()
    const dashboardStore = useDashboardStore()
    userSettingsStore.updateSettings(
      { 'trilogyResolver': 'http://localhost:5678' ,
        'theme': 'light'
      }
    )
    const modelStore = useModelConfigStore()

    const resolver = new TrilogyResolver(userSettingsStore)
    const queryExecutionService = new QueryExecutionService(
      resolver,
      connectionStore,
      modelStore,
      editorStore
    )

    provide('editorStore', editorStore)
    provide('connectionStore', connectionStore)
    provide('userSettingsStore', userSettingsStore)
    provide('queryExecutionService', queryExecutionService)
    provide('dashboardStore', useDashboardStore)

    const loaded = ref(false)
    const loadingDatabase = ref(false)
    const loadingMessage = ref('')
    const loadError = ref('')
    const dashboardId = ref('')
    const queryResults = ref<Array<{ id: string, name: string }>>([])
    const dashboardItems = ref<Array<any>>([])

    const dashboardBase = ref<InstanceType<typeof DashboardBase>>()
    const connectionId = 'portfolio-query'

    if (!editorStore) {
      throw new Error('Editor store not provided')
    }

    let connection: DuckDBConnection
    if (!connectionStore.connections[connectionId]) {
      connection = connectionStore.newConnection(connectionId, 'duckdb', {}) as DuckDBConnection
    } else {
      connection = connectionStore.connections[connectionId] as DuckDBConnection
    }


    const formatChartTitle = (name: string) => {
      return name.charAt(0).toUpperCase() + name.slice(1) + ' Analysis'
    }

    const loadDatabase = async () => {
      loadingDatabase.value = true
      loadError.value = ''
      loaded.value = false
      queryResults.value = []
      loadingMessage.value = 'Initializing...'

      try {
        const model = await loadTrilogyModels(
          modelStore,
          editorStore,
          connectionId,
          (message) => { loadingMessage.value = message }
        )

        connection.setModel(model)

        await loadPortfolioDatabase(
          props.portfolioName,
          connection,
          (message) => { loadingMessage.value = message }
        )

        let dashboard = dashboardStore.getDashboardByName(props.portfolioName)
        if (!dashboard) {
          dashboard = dashboardStore.newDashboard(props.portfolioName, connectionId)
        }

        dashboardStore.updateDashboardImports(dashboard.id, [
          {
            id: editorStore.getEditorByName('entrypoint')?.id || '-1',
            name: 'entrypoint',
            alias: '',
          }
        ])

        dashboardId.value = dashboard.id

        const reportQueries = {
          'Portfolio Summary': `SELECT sum(holdings.value) as total_holding_value, sum(dividend.amount) as total_dividend, holdings.symbol.id.count as total_holdings;`,
          'Sector Breakdown': `SELECT symbol.sector, symbol.industry, sum(holdings.value) as sector_holding_value, sum(dividend.amount) as sector_dividend;`,
          'Industry Percent of Portfolio': `import std.display; SELECT symbol.industry, (sum(holdings.value)/ sum(holdings.value) by *)::float::percent as percent_of_total, coalesce((sum(dividend.amount)/ sum(dividend.amount) by *),0)::float::percent as percent_of_all_dividends;`,
          'Top Tickers': `SELECT symbol.ticker, sum(holdings.value) as ticker_holding_value, coalesce(sum(dividend.amount),0) as ticker_dividend order by ticker_holding_value desc limit 50;`
        }

        // Execute each query and collect results
        dashboardStore.clearDashboardItems(dashboard!.id)
        for (const [queryName, queryText] of Object.entries(reportQueries)) {
          loadingMessage.value = `Executing ${queryName} query...`

          const resultEditorId = await executePortfolioQuery(
            editorStore,
            queryExecutionService,
            connectionId,
            queryName,
            queryText
          )

          queryResults.value.push({
            id: resultEditorId,
            name: queryName

          })

          let itemId = dashboardStore.addItemToDashboard(dashboard!.id, CELL_TYPES.CHART,
            undefined, undefined, undefined, undefined, queryText, queryName
          )
          dashboardItems.value.push({
            id: itemId,
          })

          console.log(dashboardStore.dashboards[dashboard!.id])
        }

        loaded.value = true
        dashboardBase.value?.handleRefresh()
      } catch (err: any) {
        console.error('Setup failed:', err)
        loadError.value = err.response?.data?.detail || err.message || 'Failed to initialize portfolio analytics'
      } finally {
        loadingDatabase.value = false
      }
    }

    const retryLoad = () => {
      loadError.value = ''
      loadDatabase()
    }

    onMounted(() => {
      loadDatabase()
    })

    const name = props.portfolioName
    return {
      editorStore,
      loaded,
      loadingDatabase,
      loadingMessage,
      loadError,
      queryResults,
      retryLoad,
      formatChartTitle,
      connectionId,
      name,
      dashboardBase,
      dashboardId,
      dashboardItems
    }
  }
}
</script>

<style scoped>
.query-container {
  padding: 20px;
  min-height: 500px;
}

.loading-state,
.initializing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  min-height: 500px;
  justify-content: center;
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

.initializing-state {
  font-size: 16px;
  color: #999;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 40px;
  background-color: #fff5f5;
  border: 1px solid #feb2b2;
  border-radius: 8px;
  max-width: 500px;
  margin: 0 auto;
}

.error-icon {
  font-size: 48px;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: #c53030;
}

.error-text {
  color: #c53030;
  font-size: 14px;
  text-align: center;
  line-height: 1.5;
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s, transform 0.1s;
}

.retry-button:hover {
  background-color: #2980b9;
}

.retry-button:active {
  transform: translateY(1px);
}

.retry-icon {
  font-size: 18px;
  font-weight: bold;
}

.data-display {
  width: 100%;
  height: 100%;
}

.dashboard-mobile-container {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  width: 100%;
  font-size: var(--font-size);
  color: var(--text-color);
  background-color: var(--bg-color);
  overflow: hidden;
}


.chart-section {
  margin-bottom: 40px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  height: 500px;
}

.chart-section:last-child {
  margin-bottom: 0;
}

.chart-title {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  text-align: center;
}
</style>