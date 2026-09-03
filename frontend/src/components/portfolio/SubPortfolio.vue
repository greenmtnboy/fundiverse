<template>
  <v-list-item>
    <template v-slot:prepend>
      <ProviderIcon :iconType="portfolio.provider" />
    </template>
    <v-list-item-title>
      {{ portfolio.name }}
      <v-tooltip v-if="statusChip">
        <template v-slot:activator="{ props }">
          <v-chip
            v-bind="props"
            :color="statusChip.color"
            size="x-small"
            label
            variant="flat"
            class="ml-2"
            :data-testid="`status-${portfolio.provider}`"
          >
            {{ statusChip.label }}
          </v-chip>
        </template>
        <span>{{ statusChip.detail }}</span>
      </v-tooltip>
      <v-tooltip v-else>
        <template v-slot:activator="{ props }">
          <span
            v-bind="props"
            class="text-medium-emphasis ml-2"
            style="font-size: small"
            :data-testid="`age-${portfolio.provider}`"
          >
            {{ relativeAge }}
          </span>
        </template>
        <span>Holdings as of {{ lastRefreshed }}</span>
      </v-tooltip>
    </v-list-item-title>
    <span>
      <CurrencyItem
        :loading="portfolio.loading"
        :value="{ currency: '$', value: portfolioSum }"
      />
      ({{ Math.round((portfolioSum / portfolioTotal) * 100) }}% of total) in {{ portfolioLength }} stocks
    </span>
    <v-spacer></v-spacer>
    <span class="text-medium-emphasis">
      <CurrencyItem :loading="portfolio.loading" :value="portfolio.cash" /> cash
    </span>
    <template v-slot:append>
      <!-- <v-chip
        v-if="portfolio.profit_or_loss"
        :color="portfolioColor"
        small
        outlined
      >
        <span class="pr-2">Return: </span>
        <CurrencyItem :value="portfolio.profit_or_loss" />
      </v-chip> -->
      <v-tooltip>
        <template v-slot:activator="{ props }">
          <v-chip
            v-if="portfolio.profit_or_loss"
            v-bind="props"
            :color="portfolioColor"
            small
            outlined
          >
            <span class="pr-2">Return: </span>
            <CurrencyItem
              :value="
                portfolio.profit_or_loss.value
                  ? portfolio.profit_or_loss
                  : { currency: 'USD', value: portfolio.profit_or_loss }
              "
            />
          </v-chip>
        </template>
        <span
          >Dividends:
          <CurrencyItem
            v-if="portfolio.dividends"
            :value="portfolio.dividends"
          />
          Appreciation:
          <CurrencyItem
            v-if="portfolio.appreciation"
            :value="portfolio.appreciation"
          />
        </span>
      </v-tooltip>

      <v-spacer />
      <ProviderLoginPopup
        stateful
        :provider="portfolio.provider"
        :portfolioName="parentName"
      ></ProviderLoginPopup>
      <!-- <v-btn v-if="loggedIn" color="green" icon="mdi-check" variant="text"></v-btn> -->
      <!-- <v-btn v-else color="grey-lighten-1" icon="mdi-login" variant="text"></v-btn> -->
      <v-spacer />
      <v-tooltip>
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            :loading="loading"
            :disabled="!loggedIn"
            @click="refresh"
            color="blue"
            icon="mdi-refresh"
            density="compact"
            variant="text"
            :data-testid="`refresh-${portfolio.provider}`"
          />
        </template>
        <span v-if="loggedIn">Refresh only this provider</span>
        <span v-else>Authenticate to refresh this provider</span>
      </v-tooltip>
      <v-spacer />
      <v-btn
        @click="removeProvider"
        color="red"
        prependIcon="mdi-cancel"
        variant="text"
      >
        Remove
      </v-btn>
    </template>
  </v-list-item>
</template>

<script lang="ts">
import CurrencyItem from "../generic/CurrencyItem.vue";
import ProviderIcon from "../icons/ProviderIcon.vue";
import ProviderLoginPopup from "/src/components/portfolio/ProviderLoginPopup.vue";
import SubPortfolioModel, {
  ProviderStatus,
} from "/src/models/SubPortfolioModel";
export default {
  data() {
    return {
      selfLoading: false,
      // drives the relative-age display; without it "just now" would still
      // read "just now" an hour later
      now: Math.floor(Date.now() / 1000),
      ageTimer: null as ReturnType<typeof setInterval> | null,
    };
  },
  mounted() {
    this.ageTimer = setInterval(() => {
      this.now = Math.floor(Date.now() / 1000);
    }, 30000);
  },
  unmounted() {
    if (this.ageTimer) {
      clearInterval(this.ageTimer);
    }
  },
  components: {
    CurrencyItem: CurrencyItem,
    ProviderIcon: ProviderIcon,
    ProviderLoginPopup: ProviderLoginPopup,
  },
  methods: {
    removeProvider() {
      this.$store.dispatch("removeProvider", {
        portfolioName: this.parentName,
        provider: this.portfolio.provider,
      });
    },
  },
  props: {
    parentName: {
      type: String,
      required: false,
      default: "",
    },
    portfolio: {
      type: SubPortfolioModel,
      required: true,
    },
    refresh: {
      type: Function,
      required: false,
      default: () => {},
    },
    portfolioTotal: {
      type: Number,
      required: false,
      default: 0,
    }
  },
  computed: {
    loading() {
      return this.portfolio.loading;
    },
    loggedIn(): boolean {
      return this.$store.getters.activeProviders.includes(
        this.portfolio.provider,
      );
    },
    lastRefreshed(): string {
      if (!this.portfolio.refreshed_at) {
        return this.portfolio.holdings.length ? "an unknown time" : "never";
      }
      return new Date(this.portfolio.refreshed_at * 1000).toLocaleString();
    },
    /**
     * How old this provider's numbers are.
     *
     * Age, not a per-refresh flag: skipping a provider in one refresh does not
     * make data fetched a minute ago any less current, so freshness is
     * measured against the clock rather than against the last button press.
     */
    relativeAge(): string {
      if (!this.portfolio.refreshed_at) {
        return this.portfolio.holdings.length ? "" : "never refreshed";
      }
      const seconds = Math.max(0, this.now - this.portfolio.refreshed_at);
      if (seconds < 90) {
        return "just now";
      }
      const units: Array<[number, string]> = [
        [60, "m"],
        [3600, "h"],
        [86400, "d"],
      ];
      let [size, suffix] = units[0];
      units.forEach(([unitSize, unitSuffix]) => {
        if (seconds >= unitSize) {
          size = unitSize;
          suffix = unitSuffix;
        }
      });
      return `${Math.floor(seconds / size)}${suffix} ago`;
    },
    /**
     * Badge for a provider we could not reach. Providers that are simply not
     * live this instant get an age instead - a badge here means action is
     * needed.
     */
    statusChip(): { label: string; color: string; detail: string } | null {
      switch (this.portfolio.status) {
        case ProviderStatus.UNAUTHENTICATED:
          return {
            label: "Not authenticated",
            color: "warning",
            detail:
              this.portfolio.error ||
              `Showing holdings as of ${this.lastRefreshed}. Log in to refresh or trade here.`,
          };
        case ProviderStatus.ERROR:
          return {
            label: "Refresh failed",
            color: "error",
            detail:
              this.portfolio.error ||
              `Showing holdings as of ${this.lastRefreshed}.`,
          };
        default:
          return null;
      }
    },
    portfolioSum() {
      return Number(
        this.portfolio.holdings.reduce(
          (sum, holding) =>
            BigInt(sum + BigInt(Math.floor(holding.value.value * 10000))) >>
            BigInt(0),
          BigInt(0),
        ) / BigInt(10000),
      );
    },
    portfolioLength() {
      return this.portfolio.holdings.length;
    },
    portfolioColor() {
      if (this.portfolio.profit_or_loss.value > 0) {
        return "green";
      } else if (this.portfolio.profit_or_loss.value < 0) {
        return "red";
      }
      return "gray";
    },
  },
};
</script>
