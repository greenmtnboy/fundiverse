<template>
  <div class="portfolio-analytics-container">
    <div class="header-section">
      <button 
        @click="refreshDatabase" 
        :disabled="loadingDatabase || refreshingDatabase" 
        class="dashboard-refresh-button"
      >
        <span class="refresh-icon" :class="{ spinning: refreshingDatabase }">↻</span>
        {{ refreshingDatabase ? 'Refreshing...' : 'Refresh Database' }}
      </button>
    </div>

    <div v-if="loadingDatabase || refreshingDatabase" class="loading-state">
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

    <div v-else-if="!loaded" class="initializing-state">
      Initializing...
    </div>

    <!-- Only render the dashboard component when everything is ready -->
    <PortfolioDashboard
      v-else
      :dashboard-id="dashboardId"
      :connection-id="connectionId"
    />
  </div>
</template>

<script lang="ts">
import { ref, onMounted, provide } from 'vue'
import { 
  useEditorStore,
  useConnectionStore, 
  useModelConfigStore, 
  useDashboardStore, 
  useUserSettingsStore,
  QueryExecutionService,
  TrilogyResolver,
} from '@trilogy-data/trilogy-studio-components/stores'
import { DuckDBConnection } from '@trilogy-data/trilogy-studio-components/connections'
import { 
  loadTrilogyModels, 
  loadPortfolioDatabase, 
  exportPortfolioDatabase 
} from '../helpers/portfolioAnalytics'
import PortfolioDashboard from './PortfolioDashboard.vue'
import { CELL_TYPES } from '@trilogy-data/trilogy-studio-components/dashboard'

interface QueryConfig {
  name: string
  query: string
  height: number
  chartConfig?: any
}

const REPORT_QUERIES: QueryConfig[] = [
  {
    name: 'Portfolio Summary',
    query: `import std.display; SELECT sum(holdings.value) as total_holding_value, sum(dividend.amount) as total_dividend, sum(holdings.appreciation) as total_appreciation, (total_appreciation/(total_holding_value-total_appreciation))::float::percent as holding_return, holdings.symbol.id.count as total_holdings;`,
    height: 150
  },
    {
    name: 'Provider Breakdown',
    query: `import std.display; SELECT holdings.provider.name, sum(holdings.value) as total_holding_value, sum(dividend.amount) as total_dividend, sum(holdings.appreciation) as total_appreciation, (total_appreciation/(total_holding_value-total_appreciation))::float::percent as holding_return, holdings.symbol.id.count as total_holdings;`,
    height: 150
  },
  {
    name: 'Cost Basis',
    query: `SELECT symbol.holding_size,
    -- case when symbol.holding_size = 'Micro' then 1
          when symbol.holding_size = 'Small' then 2
          when symbol.holding_size = 'Medium' then 3
          when symbol.holding_size = 'Large' then 4
          else 5 end as holding_size_order,
     order by holding_size_order asc;`,
    height: 150
  },
  {
    name: 'Sector Breakdown',
    query: `SELECT symbol.sector, symbol.industry, sum(holdings.value) as sector_holding_value, sum(dividend.amount) as sector_dividend;`,
    height: 500
  },
  {
    name: 'Industry Percent of Portfolio',
    query: `import std.display; SELECT symbol.industry, (sum(holdings.value)/ sum(holdings.value) by *)::float::percent as percent_of_total, coalesce((sum(dividend.amount)/ sum(dividend.amount) by *),0)::float::percent as percent_of_all_dividends;`,
    height: 500
  },
  {
    name: 'Top Tickers',
    query: `SELECT symbol.ticker, sum(holdings.value) as ticker_holding_value, coalesce(sum(dividend.amount),0) as ticker_dividend order by ticker_holding_value desc limit 50;`,
    height: 500
  },
  {
    name: 'Top Tickers Performance',
    query: `import std.display; SELECT symbol.ticker, sum(holdings.value) as ticker_holding_value, sum(holdings.appreciation) as ticker_appreciation, coalesce(sum(dividend.amount),0) as ticker_dividend, (ticker_dividend/ticker_holding_value)::float::percent as dividend_yield, ticker_dividend+ticker_appreciation as total_profit, case when total_profit > 0 then log(total_profit) when total_profit = 0 then 0.0 else -1 * log(abs(total_profit)) END as log_profit order by ticker_appreciation desc;`,
    height: 500,
    chartConfig: { 
      chartType: 'point', 
      xField: 'log_profit', 
      yField: 'ticker_holding_value', 
      annotationField: 'symbol_ticker', 
      colorField: 'dividend_yield', 
      scaleY: 'log' 
    }
  }
]

export default {
  name: 'PortfolioAnalytics',
  components: {
    PortfolioDashboard,
  },
  props: {
    portfolioName: {
      type: String,
      required: true
    }
  },
  setup(props) {
    // Store initialization
    const editorStore = useEditorStore()
    const connectionStore = useConnectionStore()
    const userSettingsStore = useUserSettingsStore()
    const dashboardStore = useDashboardStore()
    const modelStore = useModelConfigStore()

    // Initialize user settings
    userSettingsStore.updateSettings({
      'trilogyResolver': 'https://trilogy-service.fly.dev',
      'theme': 'light'
    })

    // Services setup
    const resolver = new TrilogyResolver(userSettingsStore)
    const queryExecutionService = new QueryExecutionService(resolver, connectionStore)

    // Provide dependencies for child components
    provide('editorStore', editorStore)
    provide('connectionStore', connectionStore)
    provide('userSettingsStore', userSettingsStore)
    provide('queryExecutionService', queryExecutionService)
    provide('dashboardStore', useDashboardStore)

    // Component state
    const loaded = ref(false)
    const loadingDatabase = ref(false)
    const refreshingDatabase = ref(false)
    const loadingMessage = ref('')
    const loadError = ref('')
    const dashboardId = ref('')

    const connectionId = 'portfolio-query'

    // Validate required dependencies
    if (!editorStore) {
      throw new Error('Editor store not provided')
    }

    // Initialize or get connection
    let connection: DuckDBConnection
    if (!connectionStore.connections[connectionId]) {
      connection = connectionStore.newConnection(connectionId, 'duckdb', {}) as DuckDBConnection
    } else {
      connection = connectionStore.connections[connectionId] as DuckDBConnection
    }

    // Database loading logic
    const loadDatabase = async () => {
      loadingDatabase.value = true
      loadError.value = ''
      loaded.value = false
      loadingMessage.value = 'Initializing...'

      try {
        // Load trilogy models
        const model = await loadTrilogyModels(
          modelStore,
          editorStore,
          connectionId,
          (message) => { loadingMessage.value = message }
        )

        connection.setModel(model)

        // Load portfolio database
        await loadPortfolioDatabase(
          props.portfolioName,
          connection,
          (message) => { loadingMessage.value = message }
        )

        // Get or create dashboard
        let dashboard = dashboardStore.getDashboardByName(props.portfolioName)
        if (!dashboard) {
          dashboard = dashboardStore.newDashboard(props.portfolioName, connectionId)
        }

        // Setup entrypoint content
        const entrypoint = editorStore.getEditorByName('entrypoint')
        if (entrypoint) {
          const additionalContent = `\n auto ticker_value <- sum(holdings.cost_basis) by symbol.ticker; property symbol.ticker.holding_size <- CASE WHEN ticker_value > 10000 THEN 'Large' WHEN ticker_value > 5000 THEN 'Medium' WHEN ticker_value > 100 THEN 'Small' ELSE 'Micro' END;`
          entrypoint.setContent(entrypoint.contents + additionalContent)
        }

        // Update dashboard imports
        dashboardStore.updateDashboardImports(dashboard.id, [
          {
            id: entrypoint?.id || '-1',
            name: 'entrypoint',
            alias: '',
          }
        ])

        dashboardId.value = dashboard.id

        // Clear existing dashboard items and execute queries
        dashboardStore.clearDashboardItems(dashboard.id)

        for (const queryConfig of REPORT_QUERIES) {
          loadingMessage.value = `Preparing ${queryConfig.name} chart...`

          const layoutHeight = Math.max(Math.ceil(queryConfig.height / 30), 4)

          // Add item to dashboard
          const itemId = dashboardStore.addItemToDashboard(
            dashboard.id, 
            CELL_TYPES.CHART,
            0,
            0,
            20,
            layoutHeight,
            queryConfig.query, 
            queryConfig.name
          )

          // Apply chart config if provided
          if (queryConfig.chartConfig) {
            dashboardStore.updateItemChartConfig(
              dashboard.id,
              itemId,
              queryConfig.chartConfig
            )
          }
        }

        loaded.value = true

      } catch (err: any) {
        console.error('Setup failed:', err)
        loadError.value = err.response?.data?.detail || err.message || 'Failed to initialize portfolio analytics'
      } finally {
        loadingDatabase.value = false
      }
    }

    const refreshDatabase = async () => {
      refreshingDatabase.value = true
      loadError.value = ''
      loadingMessage.value = 'Exporting new database...'

      try {
        await exportPortfolioDatabase(
          props.portfolioName,
          (message) => { loadingMessage.value = message }
        )

        loadingMessage.value = 'Reloading data...'
        await loadDatabase()
      } catch (err: any) {
        console.error('Refresh failed:', err)
        loadError.value = err.response?.data?.detail || err.message || 'Failed to refresh portfolio database'
      } finally {
        refreshingDatabase.value = false
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
      // State
      loaded,
      loadingDatabase,
      refreshingDatabase,
      loadingMessage,
      loadError,
      dashboardId,
      connectionId,
      
      // Methods
      retryLoad,
      refreshDatabase,
    }
  }
}
</script>

<style scoped>
.portfolio-analytics-container {
  padding: 20px;
  min-height: 500px;
}

.header-section {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.dashboard-refresh-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s, transform 0.1s;
}

.dashboard-refresh-button:hover:not(:disabled) {
  background-color: #218838;
}

.dashboard-refresh-button:active:not(:disabled) {
  transform: translateY(1px);
}

.dashboard-refresh-button:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.refresh-icon {
  font-size: 18px;
  font-weight: bold;
  display: inline-block;
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
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
</style>
