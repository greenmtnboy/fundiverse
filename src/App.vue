<template>
  <v-app>

      <v-app-bar color="primary" density="compact" >
        <v-app-bar-title >Fundiverse
           <!-- <span class = "text-subtitle-1">Don't pick a stock. Picks lots of stocks. </span> -->
        </v-app-bar-title>
        <v-spacer></v-spacer>
        <p class=" d-flex justify-center text-center">Don't pick a stock. Picks lots of stocks.</p>
        <v-spacer></v-spacer>
        <template v-slot:append>
          <v-icon v-if="isLoggedIn"  color="success">mdi-check</v-icon>

          <v-tooltip v-else>
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" color="warning">mdi-exclamation</v-icon>
            </template>
            <span>Must re-login to {{ provider }}!</span>
          </v-tooltip>
          <p >{{provider}}</p>
          <!-- <v-tooltip>
            <template v-slot:activator="{ props }"> -->
          <v-btn v-if="showLoginNav"  @click="gotoLogin()" icon density="compact">
            <v-icon>mdi-login</v-icon>
          </v-btn>
          <!-- </template>
            <span>Login</span>
          </v-tooltip> -->

        </template></v-app-bar>
        <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>
import axios from 'axios';
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
    ...mapActions(['setLoggedIn',]),
    gotoLogin() {
      this.$router.push({ path: '/' })
    },
    checkLogin() {
      return axios.get('http://localhost:3000/logged_in').then((response) => {
        if (response.data) { 
          this.setLoggedIn({'provider':response.data}); }
      });
    }
  },
  mounted() {
    this.checkLogin()
  },
}
</script>
<!-- 
<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style> -->
