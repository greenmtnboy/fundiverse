<template>
  <v-app>
    <v-main>
      <v-app-bar        color="primary"
        density="compact">       
        
        <template v-slot:append>
        <v-btn @click="gotoLogin()" icon density="compact">
          <v-icon>mdi-login</v-icon>
        </v-btn >
      </template></v-app-bar>
      <router-view/>
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
