<template>
    <CompositePortfolioManagementView :portfolioName="portfolioName"/>
  </template>
  
  <script>
  // @ is an alias to /src
  import CompositePortfolioManagementView from '@/components/CompositePortfolioManagementView.vue'
  
  export default {
    name: 'CompositePortfolioView',
    components: {
      CompositePortfolioManagementView
    },
    props: {
      portfolioName: String
    }
  }
  </script>
  