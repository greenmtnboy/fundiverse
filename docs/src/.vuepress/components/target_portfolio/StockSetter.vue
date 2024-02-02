<template>
    <v-card title="Stock Settings" theme="dark">
        <v-card-text>
            <p class="pb-4">
                You can exclude a stock entirely with the below toggle, or scale the weighting of the stock in the index
                by some percent. The default 100% would not change the weight in the index.
            </p>

            <v-text-field class="pb-2" v-model="ticker" label="Ticker" color="blue-darken-4" density="compact" hide-details
                variant="solo" inline inset></v-text-field>
            <v-switch v-model="excluded" class="pb-2"
                :label="excluded ? 'Toggle inclusion. Currently this stock will be excluded.' : 'Toggle inclusion. Currently this stock will be included.'"
                color="blue-darken-4" density="compact" hide-details inline inset></v-switch>
            <v-text-field v-model="weight" :disabled="excluded" label="Weighting %" variant="solo" color="blue-darken-4"
                density="compact" :rules="numberValidationRules" hide-details inline inset></v-text-field>
            <!-- <v-text-field v-model="minWeight" :disabled="excluded" :rules="numberValidationRules" color="blue-darken-4" label="Minimum Weighting" density="compact" variant="solo" hide-details inline inset></v-text-field> -->
        </v-card-text>
        <v-divider></v-divider>

        <v-card-actions class="justify-center px-6 py-3">
            <v-btn :disabled="!hasValidChanges" class="text-white flex-grow-1 text-none" color="primary" variant="flat"
                @click="submit()">
                Submit
            </v-btn>
        </v-card-actions>
    </v-card>
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
        submit() {
            if (this.excluded) {
                this.excludeStock({ portfolioName: this.portfolioName, ticker: this.ticker })
            } else {
                this.modifyStock({
                    'portfolioName': this.portfolioName,
                    'ticker': this.ticker,
                    'scale': this.weight / 100,
                    // 'minWeight': this.minWeight
                })
            }
            this.dialog = false;
        }
    }
}
</script>
