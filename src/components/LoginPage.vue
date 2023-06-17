<template>
  <v-card class="mx-auto" max-width="344" title="Login to Provider">
    <v-form v-model="form" @submit.prevent="onSubmit">
      <v-container>

        <v-select :readonly="loading" :rules="[required]" v-model="first" color="primary"
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

export default {
  name: "LoginPage",
  data() {
    return {
      providers: [],
      selectedProvider: null,
      form: false,
      key: '',
      secret: ''

    };
  },
  computed: {
  },
  methods: {
    onSubmit() {
      if (!this.form) return

      this.loading = true

      setTimeout(() => (this.loading = false), 2000)
    },
    required(v) {
      return !!v || 'Field is required'
    },
    getProviders() {
      return axios.get('http://localhost:3000/providers').then((response) => {
        this.providers = response.data.available;
        // const transformedMap = new Map();

        // Object.keys(response.data.loaded).forEach((key) => {
        //   const transformedValue = parse_target_portfolio_model(response.data.loaded[key])
        //   transformedMap.set(key, transformedValue);
        // });
        // this.targetPortfolios = new TargetPortfolioListModel({ loaded: transformedMap });
        // this.selectedIndex = Array.from(this.targetPortfolios.loaded.keys())[0];
      });
    },

    login(username, password) {
      let local = this;
      return axios.post('http://localhost:3000/login',
        { 'key': username, 'secret': password }).then(() => {
          local.$router.push.push({ path: 'portfolio' })
        });
    },
  },
  mounted() {
    this.getProviders()
  },
};
</script>