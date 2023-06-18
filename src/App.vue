<template>
  <v-app>

      <v-app-bar color="primary" density="compact" >
        <v-app-bar-title>Fundiverse</v-app-bar-title>
        <p>Don't pick stocks. Picks lots of stocks.</p>

        <template v-slot:append>
          <v-icon v-if="isLoggedIn()" color="success">mdi-check</v-icon>
          <v-tooltip v-else>
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" color="warning">mdi-exclamation</v-icon>
            </template>
            <span>Must login to use tool!</span>
          </v-tooltip>
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
import { mapActions } from 'vuex';
export default {
  name: 'App',

  components: {
  },

  data: () => ({
    loggedIn: false,

  }),
  computed: {
    showLoginNav() {
      return this.$route.name !== 'login';
    },
  },
  methods: {
    ...mapActions(['setLoggedIn',]),
    gotoLogin() {
      this.$router.push({ path: '/' })
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
    checkLogin() {
      return axios.get('http://localhost:3000/logged_in').then((response) => {
        console.log(response.data)
        
        if (response.data.logged_in === 'true') { this.setLoggedIn(); }
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
