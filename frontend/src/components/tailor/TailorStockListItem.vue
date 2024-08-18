<template>
  <v-list-item>
    <v-list-item-title
      ><span class="px-1"><TickerDisplay :ticker="ticker" /></span>
      <v-chip :color="scale >= 1 ? 'green' : 'red'" v-if="scale" small outlined
        >{{ scale * 100 }}%</v-chip
      >
    </v-list-item-title>
    <template v-slot:append>
      <v-tooltip>
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            @click="localRemoveStockExclusion(ticker)"
            icon
            density="compact"
          >
            <v-icon color="warning">mdi-cancel</v-icon>
          </v-btn>
        </template>
        <span v-if="mode=='exclusion'">Remove Exclusion</span>
        <span v-else="mode=='exclusion'">Remove Modification</span>
      </v-tooltip>
    </template>
  </v-list-item>
</template>

<script lang="ts">
import { mapActions } from "vuex";
import TickerDisplay from "../generic/TickerDisplay.vue";
export default {
  name: "TailorComponentStockItem",
  data() {
    return {};
  },
  components: { TickerDisplay },
  props: {
    ticker: {
      type: String,
      required: true,
    },
    scale: {
      type: Number,
      required: false,
    },
    portfolioName: {
      type: String,
      required: true,
    },
    mode: {
      type: String,
      required: false,
      default: "exclusion",
    },
  },
  computed: {},
  methods: {
    ...mapActions(["removeStockExclusion"]),
    localRemoveStockExclusion(data) {
      this.removeStockExclusion({
        portfolioName: this.portfolioName,
        ticker: data,
        mode: this.mode,
      });
    },
  },
};
</script>
