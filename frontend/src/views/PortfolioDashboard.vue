<template>
  <div class="dashboard-container">
    <div v-if="!dashboardReady" class="initializing-state">
      Setting up dashboard...
    </div>

    <div v-else class="data-display">
      <div class="dashboard-mobile-container">
        <div 
          v-for="item in dashboardItems" 
          :key="item.id" 
          class="chart-section"
          :style="{ height: item.height + 'px' }"
        >
          <DashboardChart 
            :dashboardId="dashboardId" 
            :itemId="item.id" 
            :setItemData="setItemData"
            :getItemData="getItemData" 
            :editMode="false"
            :getDashboardQueryExecutor="getDashboardQueryExecutor"
            :symbols="[]"
            @dimension-click="setCrossFilter" 
            @background-click="() => unSelect(item.id)" 
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { ref, computed, watch, inject, onMounted } from 'vue'
import { useDashboardStore } from 'trilogy-studio-components/stores'
import DashboardChart from 'trilogy-studio-components/components/dashboard/DashboardChart.vue'
import { useDashboard } from 'trilogy-studio-components/components/dashboard/useDashboard'

interface DashboardItem {
  id: string
  height: number
}

export default {
  name: 'PortfolioDashboard',
  components: {
    DashboardChart,
  },
  props: {
    portfolioName: {
      type: String,
      required: true
    },
    dashboardId: {
      type: String,
      required: true
    },
    dashboardItems: {
      type: Array as () => DashboardItem[],
      required: true
    },
    connectionId: {
      type: String,
      required: true
    }
  },
  emits: ['fullScreen'],
  setup(props, { emit }) {
    const dashboardStore = useDashboardStore()
    const queryExecutionService = inject('queryExecutionService')

    if (!queryExecutionService) {
      throw new Error('QueryExecutionService not provided')
    }

    // Get the dashboard from the store
    const dashboard = computed(() => {
      return Object.values(dashboardStore.dashboards).find((d) => d.id === props.dashboardId) || null
    })

    // Layout update handler
    const onLayoutUpdated = (newLayout: any) => {
      // Handle layout updates if needed
      console.log('Layout updated:', newLayout)
    }

    // Initialize dashboard functionality using useDashboard composable
    // This can be called in setup because the dashboard is guaranteed to exist
    const dashboardFunctionality = useDashboard(
      dashboard,
      {
        isMobile: false,
      },
      {
        layoutUpdated: (newLayout) => onLayoutUpdated(newLayout),
        dimensionsUpdate: (itemId) => {},
        triggerResize: () => {},
        fullScreen: (enabled) => emit('fullScreen', enabled),
      },
      queryExecutionService,
    )

    const dashboardReady = ref(false)

    // Watch for when dashboard becomes available and refresh
    watch(dashboard, (newDashboard) => {
      if (newDashboard) {
        console.log('Dashboard available, refreshing:', newDashboard.id)
        // dashboardFunctionality.onRefresh()
        dashboardReady.value = true
      }
    }, { immediate: true })

    // Refresh on mount to ensure data is loaded
    onMounted(() => {
      if (dashboard.value) {
        console.log('Component mounted, refreshing dashboard')
        dashboardFunctionality.handleRefresh()
      }
    })

    return {
      dashboardReady,
      
      // Dashboard methods from useDashboard
      getDashboardQueryExecutor: dashboardFunctionality.getDashboardQueryExecutor,
      getItemData: dashboardFunctionality.getItemData,
      setItemData: dashboardFunctionality.setItemData,
      setCrossFilter: dashboardFunctionality.setCrossFilter,
      unSelect: dashboardFunctionality.unSelect,
      handleRefresh: dashboardFunctionality.handleRefresh,
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  width: 100%;
  height: 100%;
}

.initializing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  min-height: 200px;
  justify-content: center;
  font-size: 16px;
  color: #999;
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
  /* margin-bottom: 40px; */
  /* padding: 20px; */
  background-color: #f8f9fa;
  border-radius: 0px;
  /* border: 1px solid #e0e0e0; */
}

.chart-section:last-child {
  margin-bottom: 0;
}
</style>