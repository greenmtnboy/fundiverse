<template>
  <v-app>

    <v-app-bar color="primary" density="compact">
      <v-app-bar-title>Fundiverse
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <p class=" d-flex justify-center text-center">Don't pick a stock. Picks lots of stocks.</p>
      <v-spacer></v-spacer>
      <template v-slot:append>
        <v-icon v-if="isLoggedIn" color="success">mdi-check</v-icon>

        <v-tooltip v-else>
          <template v-slot:activator="{ props }">
            <v-icon v-bind="props" color="warning">mdi-exclamation</v-icon>
          </template>
          <span>Must re-login to {{ provider }}!</span>
        </v-tooltip>
        <p>{{ provider }}</p>
        <v-btn v-if="showLoginNav" @click="gotoLists()" icon density="compact">
          <v-icon>mdi-login</v-icon>
        </v-btn>
        <v-btn v-if="showLoginNav" @click="gotoLogin()" icon density="compact">
          <v-icon>mdi-login</v-icon>
        </v-btn>

      </template>
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
export default {
  name: 'App',

  components: {
  },

  data: () => ({

  }),
  computed: {
    showLoginNav() {
      return this.$route.name !== 'login';
    },
    provider() {
      return this.$store.getters.provider;
    },
    ...mapGetters(['isLoggedIn'])
  },
  methods: {
    ...mapActions(['loadDefaultModifications']),
    gotoLogin() {
      this.$router.push({ path: 'login' })
    },
    gotoLists() {
      this.$router.push({ path: 'portfolio_list' })
    },
  }
}

</script>
