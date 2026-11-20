<template>
  <v-tooltip v-on:update:modelValue="load()" max-width="420">
    <template v-slot:activator="{ props }">
      <span v-bind="props">
        {{ ticker }}
      </span>
    </template>
    <div v-if="error">Error loading ticker details: {{ error }}</div>
    <div v-else-if="!info">Loading...</div>
    <div v-else class="ticker-tooltip">
      <div class="font-weight-bold">
        {{ info.name || ticker }} ({{ ticker }})
      </div>
      <div v-if="listing">{{ listing }}</div>
      <div>
        <template v-if="info.price !== null">
          {{ formatPrice(info.price) }}
          <span class="text-caption">via {{ info.price_provider }}</span>
        </template>
        <template v-else>No current price</template>
      </div>
      <div class="text-caption mt-1">
        {{ description }}
      </div>
    </div>
  </v-tooltip>
</template>
<style>
.ticker-tooltip > div + div {
  margin-top: 2px;
}
</style>
<script lang="ts">
import instance from "/src/api/instance";

interface TickerInfo {
  ticker: string;
  name: string | null;
  exchange: string | null;
  sector: string | null;
  description: string | null;
  price: number | null;
  price_provider: string | null;
}

// a tooltip shown again after this long fetches a fresh price
const PRICE_MAX_AGE_MS = 60_000;
const DESCRIPTION_LENGTH = 200;

export default {
  name: "Ticker Display",
  data() {
    return {
      info: null as TickerInfo | null,
      error: null as string | null,
      loadedAt: 0,
      loading: false,
    };
  },
  props: {
    ticker: {
      type: String,
      required: true,
    },
  },
  computed: {
    listing(): string {
      return [this.info?.exchange, this.info?.sector]
        .filter(Boolean)
        .join(" · ");
    },
    description(): string {
      const text = this.info?.description;
      if (!text) {
        return "No description available";
      }
      return text.length > DESCRIPTION_LENGTH
        ? `${text.substring(0, DESCRIPTION_LENGTH)}...`
        : text;
    },
  },
  methods: {
    formatPrice(price: number): string {
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(price);
    },
    load() {
      if (this.loading || Date.now() - this.loadedAt < PRICE_MAX_AGE_MS) {
        return;
      }
      this.loading = true;
      instance
        .get(`stock_info/${this.ticker}`)
        .then((resp) => {
          this.info = resp.data;
          this.error = null;
        })
        .catch((e) => {
          this.error = `${e}`;
        })
        .finally(() => {
          this.loading = false;
          this.loadedAt = Date.now();
        });
    },
  },
};
</script>
