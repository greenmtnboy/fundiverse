<template>
  <v-app>
    <v-main>
      <PortfolioView/>
      <!-- <HelloWorld/> -->
    </v-main>
  </v-app>
</template>

<script>
import PortfolioView from './components/PortfolioManagementView.vue';

export default {
  name: 'App',

  components: {
    PortfolioView,
},

  data: () => ({
    //
  }),
}
</script>
