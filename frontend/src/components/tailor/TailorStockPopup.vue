<template>
    <!-- rounded="0" -->
    <v-dialog v-model="dialog" max-width="500">
        <template v-slot:activator="{ props }">
            <v-btn class="text-none" color="primary" variant="outlined" v-bind="props">
                Add Stock Adjustment
            </v-btn>
        </template>

        <v-card title="Stock Settings">
            <v-card-text>
                <p class="pb-4">
                    You can exclude a stock entirely with the below toggle, or scale the
                    weighting of the stock in the index by some percent. The default 100%
                    would not change the weight in the index.
                </p>

                <v-text-field class="pb-2" v-model="ticker" label="Ticker" color="blue-darken-4" density="compact"
                    hide-details variant="solo" inline inset @update:modelValue="handleTickerInputUpdate"></v-text-field>
                <v-banner lines="two" icon="$warning" color="primary">
                    <v-banner-text v-if="updateType == 'reweight'">
                        This ticker is already in the index, you can exclude it or reweight the current % by a new %. (100%
                        would mantain currrent weight.)
                    </v-banner-text>
                    <v-banner-text v-else>
                        This ticker is not in the index, you can add it with a base % target. (1% would be 1% of your target
                        index.)
                    </v-banner-text>
                </v-banner>
                <v-switch v-if="updateType == 'reweight'" v-model="excluded" class="pb-2" :label="excluded
                    ? 'Toggle inclusion. Currently this stock will be excluded.'
                    : 'Toggle inclusion. Currently this stock will be included.'
                    " color="blue-darken-4" density="compact" hide-details inline inset></v-switch>

                <v-text-field v-model="weight" :disabled="excluded"
                    :label="updateType == 'reweight' ? 'Reweight %' : 'Target %'" variant="solo" color="blue-darken-4"
                    density="compact" :rules="numberValidationRules" hide-details inline inset></v-text-field>

            </v-card-text>
            <v-divider></v-divider>

            <v-card-actions class="justify-center px-6 py-3">
                <v-btn class="flex-grow-1 text-none" variant="plain" @click="dialog = false">
                    Exit
                </v-btn>

                <v-btn :disabled="!hasValidChanges" class="text-white flex-grow-1 text-none" color="primary" variant="flat"
                    @click="submit()">
                    Save
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts">
import {
    mapActions
} from 'vuex'
export default {
    name: "TailorStockPopup",
    data() {
        return {
            excluded: false,
            dialog: false,
            weight: 100,
            minWeight: 0,
            ticker: '',
            tickerValidated: false,
            updateType: "reweight"
        }
    },
    props: {
        portfolioName: {
            type: String,
            required: true,
        },
    },
    computed: {
        hasValidChanges() {
            return this.excluded || this.weight != 100 || this.minWeight != 0;
        },
        numberValidationRules() {
            return [
                (value) => {
                    if (!value || /^[0-9\\.]+$/.test(value)) {
                        return true;
                    }
                    return 'Only numbers are allowed.';
                }
            ];
        },
    },
    methods: {
        ...mapActions(['excludeStock', 'modifyStock']),
        handleTickerInputUpdate() {
            this.tickerValidated = false;
            if (this.portfolio.contains({ ticker: this.ticker })) {
                this.updateType = 'reweight'
                this.weight = 100

            }
            else {
                this.updateType = 'add'
                this.weight = 1
            }
            this.tickerValidated = true;
        },
        submit() {
            if (this.excluded) {
                this.excludeStock({ portfolioName: this.portfolioName, ticker: this.ticker })
            } else {
                if (this.updateType == 'add') {
                    this.modifyStock({
                    portfolioName: this.portfolioName,
                    ticker: this.ticker,
                    scale: null,
                    minWeight: this.weight /100,
                });
                }
                else {
                this.modifyStock({
                    portfolioName: this.portfolioName,
                    ticker: this.ticker,
                    scale: this.weight / 100,
                    minWeight: null,
                    // 'minWeight': this.minWeight
                });
            }
            this.dialog = false;
        }
    }
}
</script>
