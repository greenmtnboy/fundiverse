<template>
  <v-dialog v-model="dialog" max-width="500" min-width="400">
    <template v-slot:activator="{ props }">
      <v-btn
        disabled="true"
        class="text-none"
        color="primary"
        variant="outlined"
        v-bind="props"
      >
        Add New Stock List
      </v-btn>
    </template>
    <v-card class="mx-auto" min-width="344" title="New Portfolio">
      <v-form v-model="form" @submit.prevent="newPortfolio">
        <v-container>
          <v-text-field
            :readonly="loading"
            :rules="[required]"
            v-model="name"
            color="primary"
            label="New Index Name"
            variant="underlined"
          >
          </v-text-field>
        </v-container>
        <v-divider></v-divider>
        <v-alert class="mx-auto square-corners" color="warning" v-if="error">{{
          error
        }}</v-alert>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            :disabled="!form"
            :loading="loading"
            color="success"
            type="submit"
          >
            Create
            <v-icon icon="mdi-chevron-right" end></v-icon>
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card>
  </v-dialog>
</template>
<style scoped>
.square-corners {
  border-radius: 0 !important;
}
</style>
<script lang="ts">
import { mapActions } from "vuex";
export default {
  name: "AddPortfolioPopup",
  data() {
    return {
      name: "",
      form: false,
      loading: false,
      error: "",
      dialog: false,
    };
  },
  props: {},
  computed: {},
  methods: {
    ...mapActions(["addStockList"]),
    required(v) {
      return !!v || "Field is required";
    },
  },
};
</script>
