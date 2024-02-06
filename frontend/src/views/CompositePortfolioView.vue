<template>
  <CompositePortfolioManagementView :portfolioName="portfolioName" />
</template>

<script lang="ts">
// @ is an alias to /src
import CompositePortfolioManagementView from "/src/components/CompositePortfolioManagementView.vue";

export default {
  name: "CompositePortfolioView",
  components: {
    CompositePortfolioManagementView,
  },
  props: {
    portfolioName: String,
  },
};
</script>
