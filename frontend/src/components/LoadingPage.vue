<template>
     <v-sheet
    class="d-flex align-center justify-center flex-wrap text-center mx-auto px-4"
    elevation="4"
    height="100%"
    rounded
    width="100%"
  >
    <div>
      <h2 class="text-h4 font-weight-black"></h2>

      <v-progress-circular
              indeterminate
              size="64"
              color="primary"
            ></v-progress-circular>

      <p class="text-body-2 mb-4">
        Waiting for background services to start...
      </p>
    </div>
  </v-sheet>
</template>

<script lang="ts">

import instance from '../api/instance'
export default {
    name: "LoadingPage",
    data() {
        return {
        };
    },
    methods: {
        login() {
            let local = this;
            return instance.get('', {
            }).then(() => {
                local.$router.push({
                    path: 'portfolio_list'
                })

            }).catch(() => {
                setTimeout(() => {
                    local.login()
                }, 1000)
            });
        },
    },
    mounted() {
        this.login()
    },
};
</script>
