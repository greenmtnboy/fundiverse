<template>
  <v-app>
    <v-main>
      <v-app-bar color="primary" density="compact">

        <template v-slot:append>
          <v-icon v-if="isLoggedIn()" color="success">mdi-check</v-icon>
          <v-tooltip  v-else>
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" color="warning">mdi-exclamation</v-icon>
            </template>
            <span>Must login to use tool!</span>
          </v-tooltip>
          <!-- <v-tooltip>
            <template v-slot:activator="{ props }"> -->
              <v-btn v-bind="props" @click="gotoLogin()" icon density="compact">
            <v-icon>mdi-login</v-icon>
          </v-btn>
            <!-- </template>
            <span>Login</span>
          </v-tooltip> -->

        </template></v-app-bar>
      <router-view />
    </v-main>
  </v-app>
</template>

<script>

export default {
  name: 'App',

  components: {
  },

  data: () => ({
    loggedIn: false,

  }),

  methods: {
    gotoLogin() {
      this.$router.push({ path: '/' })
    },
    isLoggedIn() {
      return this.$store.getters.isLoggedIn;
    },
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
