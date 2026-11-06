<template>
  <v-dialog v-model="dialog" max-width="760" persistent scrollable>
    <template v-slot:activator="{ props }">
      <v-btn
        :disabled="disabled"
        data-testid="btn-upload-orders"
        v-bind="props"
      >
        Upload Orders
      </v-btn>
    </template>

    <v-card title="Upload Orders">
      <v-card-text>
        <template v-if="placedOrders.length">
          <p class="pb-2" data-testid="upload-orders-placed">
            {{ placedCount }} of {{ placedOrders.length }} orders placed.
            Fills depend on the market, so check each broker.
          </p>
          <OrderResult
            v-for="order in placedOrders"
            :key="`${order.provider}-${order.ticker}`"
            :element="order"
          />
        </template>

        <template v-else>
          <p class="pb-4">
            Choose a CSV with a header row: side, ticker, either shares or
            value, and optionally broker. Sells without a broker draw on the
            biggest percentage losers first. Nothing is placed until you
            confirm below.
          </p>
          <v-file-input
            v-model="file"
            label="Order file"
            accept=".csv"
            variant="underlined"
            density="compact"
            :disabled="loading || submitting"
            :loading="loading"
            data-testid="input-order-file"
            @update:modelValue="readFile"
          ></v-file-input>

          <v-alert
            v-if="errors.length"
            color="warning"
            density="compact"
            class="mb-3"
            data-testid="upload-orders-errors"
          >
            <div v-for="error in errors.slice(0, 8)" :key="error">
              {{ error }}
            </div>
            <div v-if="errors.length > 8">
              And {{ errors.length - 8 }} more.
            </div>
          </v-alert>

          <template v-if="plan">
            <v-alert
              v-if="plan.rejected.length"
              color="warning"
              density="compact"
              class="mb-3"
              data-testid="upload-orders-rejected"
            >
              <div class="font-weight-bold">
                Not every row can be placed. The orders below are all that
                would be.
              </div>
              <div
                v-for="row in plan.rejected"
                :key="`${row.ticker}-${row.reason}`"
              >
                {{ row.side }} {{ row.ticker }}: {{ row.reason }}
              </div>
            </v-alert>

            <p class="pb-2" data-testid="upload-orders-summary">
              {{ summary }}
            </p>
            <v-table density="compact" data-testid="upload-orders-preview">
              <thead>
                <tr>
                  <th>Side</th>
                  <th>Ticker</th>
                  <th>Broker</th>
                  <th class="text-right">Shares</th>
                  <th class="text-right">About</th>
                  <th class="text-right">Est. gain</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="order in plan.to_buy"
                  :key="`${order.provider}-${order.ticker}-${order.order_type}`"
                >
                  <td>{{ order.order_type }}</td>
                  <td>{{ order.ticker }}</td>
                  <td>{{ order.provider }}</td>
                  <td class="text-right">{{ order.qty ?? "" }}</td>
                  <td class="text-right">{{ dollars(estimate(order)) }}</td>
                  <td class="text-right">{{ gain(order) }}</td>
                </tr>
              </tbody>
            </v-table>
            <v-checkbox
              v-if="plan.to_buy.length"
              v-model="confirmed"
              :label="confirmLabel"
              density="compact"
              hide-details
              class="pt-2"
              data-testid="check-upload-orders-confirm"
            ></v-checkbox>
          </template>
        </template>
      </v-card-text>
      <v-divider></v-divider>

      <v-card-actions class="justify-center px-6 py-3">
        <v-btn
          class="flex-grow-1 text-none"
          variant="plain"
          :disabled="submitting"
          @click="close()"
        >
          {{ placedOrders.length ? "Close" : "Exit" }}
        </v-btn>
        <v-btn
          v-if="!placedOrders.length"
          :disabled="!plan || !plan.to_buy.length || !confirmed"
          :loading="submitting"
          class="text-white flex-grow-1 text-none"
          color="primary"
          variant="flat"
          data-testid="btn-upload-orders-submit"
          @click="submit()"
        >
          Place {{ plan ? plan.to_buy.length : "" }} Orders
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { mapActions } from "vuex";

import instance from "/src/api/instance";
import { parseOrderFile } from "/src/helpers/orderFile";
import { orderValue } from "/src/helpers/orderValue";
import OrderResult from "./OrderResult.vue";

export default {
  name: "UploadOrders",
  components: { OrderResult },
  data() {
    return {
      dialog: false,
      file: null as File | File[] | null,
      plan: null as any,
      errors: [] as string[],
      confirmed: false,
      loading: false,
      submitting: false,
      placedOrders: [] as any[],
    };
  },
  props: {
    portfolioName: {
      type: String,
      required: true,
    },
    providers: {
      type: Array,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    sells() {
      return (this.plan?.to_buy ?? []).filter(
        (order) => order.order_type === "SELL",
      );
    },
    summary() {
      const total = this.sells.reduce(
        (sum, order) => sum + this.estimate(order),
        0,
      );
      const known = this.sells.filter((order) => order.estimated_gain);
      const gain = known.reduce(
        (sum, order) => sum + Number(order.estimated_gain.value),
        0,
      );
      const unknown = this.sells.length - known.length;
      const buys = this.plan.to_buy.length - this.sells.length;
      return [
        `${this.sells.length} sells, about ${this.dollars(total)}`,
        `estimated gain ${this.dollars(gain)}`,
        unknown ? `${unknown} with no cost basis` : "",
        buys ? `${buys} buys` : "",
      ]
        .filter(Boolean)
        .join(", ");
    },
    confirmLabel() {
      return this.sells.length
        ? `Place these as market orders, selling ${this.sells.length} real positions. This can't be undone.`
        : "Place these as market orders. This can't be undone.";
    },
    placedCount() {
      return this.placedOrders.filter((order) => order.status === "placed")
        .length;
    },
  },
  methods: {
    ...mapActions(["refreshCompositePortfolio"]),
    estimate(order): number {
      return Number(orderValue(order)?.value ?? 0);
    },
    dollars(value: number): string {
      const sign = value < 0 ? "-" : "";
      return `${sign}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    },
    gain(order): string {
      if (order.order_type !== "SELL") {
        return "";
      }
      return order.estimated_gain
        ? this.dollars(Number(order.estimated_gain.value))
        : "Unknown";
    },
    reset() {
      this.plan = null;
      this.errors = [];
      this.confirmed = false;
    },
    async readFile(selected: File | File[] | null) {
      this.reset();
      const file = Array.isArray(selected) ? selected[0] : selected;
      if (!file) {
        return;
      }
      this.loading = true;
      try {
        const parsed = parseOrderFile(await file.text());
        if (parsed.errors.length) {
          this.errors = parsed.errors;
          return;
        }
        // caps come from holdings, which have to be current
        await this.refreshCompositePortfolio({
          portfolioName: this.portfolioName,
          keys: this.providers,
        });
        const response = await instance.post("plan_uploaded_orders", {
          orders: parsed.orders,
          providers: this.providers,
        });
        this.plan = response.data;
      } catch (exception: any) {
        this.errors = [
          exception?.response?.data?.detail ?? `Could not plan ${file.name}.`,
        ];
      } finally {
        this.loading = false;
      }
    },
    async submit() {
      this.submitting = true;
      try {
        const response = await instance.post(
          "buy_index_from_plan_multi_provider",
          { plan: this.plan, providers: this.providers, allow_sells: true },
        );
        this.placedOrders = response.data.orders;
        const touched = this.plan.order_providers;
        this.plan = null;
        this.confirmed = false;
        this.refreshCompositePortfolio({
          portfolioName: this.portfolioName,
          keys: this.providers,
          providersToRefresh: touched,
        });
      } catch (exception: any) {
        // the broker may have taken some of these, so don't offer a resubmit
        this.errors = [
          exception?.response?.data?.detail ??
            "Placing failed partway. Check each broker before uploading again.",
        ];
        this.plan = null;
        this.confirmed = false;
      } finally {
        this.submitting = false;
      }
    },
    close() {
      this.dialog = false;
      this.file = null;
      this.placedOrders = [];
      this.reset();
    },
  },
};
</script>
