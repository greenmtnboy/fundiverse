<template>
  <v-card class="mx-auto" max-width="344" title="Login to Provider">
    <v-form v-model="form" @submit.prevent="login">
      <v-container>

        <v-select :readonly="loading" :rules="[required]" v-model="selectedProvider" color="primary"
          :items="providers" 
          label="Provider Type"   variant="underlined"></v-select>

        <v-text-field :readonly="loading" :rules="[required]" v-model="key" color="primary"
          label="API Key"   variant="underlined"></v-text-field>

        <v-text-field :readonly="loading" :rules="[required]" v-model="secret" color="primary" label="API Secret"
          variant="underlined"></v-text-field>
      </v-container>

      <v-divider></v-divider>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :disabled="!form" :loading="loading" color="success" type="submit">
          Authenticate
          <v-icon icon="mdi-chevron-right" end></v-icon>
        </v-btn>
      </v-card-actions>
    </v-form>
  </v-card>
</template>
  
<script>
// Views

import axios from 'axios';
import { mapActions } from 'vuex';
export default {
  name: "LoginPage",
  data() {
    return {
      providers: [],
      selectedProvider: null,
      form: false,
      key: '',
      secret: '',
      loading: false,

    };
  },
  computed: {
  },
  methods: {
    ...mapActions(['setLoggedIn']),
    required(v) {
      return !!v || 'Field is required'
    },
    getProviders() {
      let local = this;
      return axios.get('http://localhost:3000/providers').then((response) => {
        local.providers = response.data.available;
        // const transformedMap = new Map();

        // Object.keys(response.data.loaded).forEach((key) => {
        //   const transformedValue = parse_target_portfolio_model(response.data.loaded[key])
        //   transformedMap.set(key, transformedValue);
        // });
        // this.targetPortfolios = new TargetPortfolioListModel({ loaded: transformedMap });
        // this.selectedIndex = Array.from(this.targetPortfolios.loaded.keys())[0];
      });
    },

    login() {
      let local = this;
      this.loading = true
      return axios.post('http://localhost:3000/login',
        { 'key': this.key, 'secret': this.secret, 'provider': this.selectedProvider}).then(() => {
          this.setLoggedIn();
          this.loading = false;
          local.$router.push({ path: 'portfolio' })

        });
    },
  },
  mounted() {
    this.getProviders()
  },
};
</script>