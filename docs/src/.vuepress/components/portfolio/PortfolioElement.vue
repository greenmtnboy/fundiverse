<template>
    <v-list-item :min-height="15">
        <div>
            <v-row>
                <v-col cols="7">
                    <TickerDisplay :ticker="ticker" />
                    <p class="text-medium-emphasis">
                        <CurrencyItem :value="value"></CurrencyItem> ({{ elementWeight }}%)
                    </p>
                </v-col>
                <v-col cols="5" class="text-right pr-10">
                    <v-tooltip>
                        <template v-slot:activator="{ props }">
                            <v-chip v-bind="props" small :color="plColor" outlined class="text-low-emphasis">
                                <CurrencyItem v-if="profit" :value="profit"> </CurrencyItem>
                            </v-chip>
                        </template>
                        <span>Dividends:
                            <CurrencyItem v-if="dividends" :value="dividends" /> Appreciation:
                            <CurrencyItem v-if="appreciation" :value="appreciation" />
                        </span>
                    </v-tooltip>
                </v-col>
            </v-row>
        </div>
        <template v-slot:append>
            <v-tooltip v-if="unsettled">
                <template v-slot:activator="{ props }">
                    <v-btn color="warning" v-bind="props" icon density="compact">
    
                        <span style="letter-spacing:inherit" class="material-icons md-12">exclamation</span>
                    </v-btn>
                </template>
                <span>This stock has unsettled orders</span>
            </v-tooltip>
            <v-btn v-else-if="!this.targetWeight" icon density="compact"> </v-btn>
            <v-tooltip v-else-if="onGoal">
                <template v-slot:activator="{ props }">
                    <v-btn color="success" v-bind="props" icon density="compact">
                        <span style="letter-spacing:inherit" class="material-icons md-12">check</span>
                    </v-btn>
                </template>
                <span>This stock is near goal ({{ targetWeightDisplay }}%)</span>
            </v-tooltip>
            <v-tooltip v-else-if="overGoal">
                <template v-slot:activator="{ props }">
                    <v-btn color="blue" v-bind="props" icon density="compact">
                        <span style="letter-spacing:inherit" class="material-icons md-12">arrow_upward</span>
                    </v-btn>
                </template>
                <span>This stock is over goal ({{ targetWeightDisplay }}%)</span>
            </v-tooltip>
            <v-tooltip v-else>
                <template v-slot:activator="{ props }">
                    <v-btn  color="orange" v-bind="props" icon density="compact">
                        <span style="letter-spacing:inherit" class="material-icons md-12">arrow_downward</span>
                    </v-btn>
                </template>
                <span>This stock is under goal ({{ targetWeightDisplay }}%)</span>
            </v-tooltip>
            <!-- <v-btn v-else icon density="compact">
            </v-btn> -->
        </template>
    </v-list-item>
</template>

<script lang="ts">
import TickerDisplay from "../generic/TickerDisplay.vue";
import CurrencyItem from "../generic/CurrencyItem.vue";
import CurrencyModel from "../models/CurrencyModel";
const comparisonThreshold = 0.1;

export default {
    name: "PortfolioElement",
    data() {
        return {
            loading: false,
        };
    },
    components: {
        CurrencyItem,
        TickerDisplay,
    },
    props: {
        ticker: {
            type: String,
            required: true,
        },
        value: {
            type: CurrencyModel,
            required: true,
        },
        targetWeight: {
            type: Number,
            required: false,
        },
        totalPortfolioSize: {
            type: Number,
            required: false,
        },
        unsettled: {
            type: Boolean,
            required: false,
        },
        appreciation: {
            type: CurrencyModel,
            required: false,
        },
        dividends: {
            type: CurrencyModel,
            required: false,
        },
    },
    computed: {
        plColor() {
            if (this.profit.value > 0) {
                return "green";
            } else if (this.profit.value < 0) {
                return "red";
            }
            return "gray";
        },
        onGoal() {
            if (!this.totalPortfolioSize) {
                return false;
            }
            return (
                Math.abs(this.elementWeight - this.targetWeightDisplay) <
                comparisonThreshold
            );
        },
        profit() {
            if (!this.dividends || !this.appreciation) {
                return new CurrencyModel({ value: 0.0, currency: "USD" });
            }
            return new CurrencyModel({
                value: Number(this.dividends.value) + Number(this.appreciation.value),
                currency: this.dividends.currency,
            });
        },
        overGoal() {
            if (!this.totalPortfolioSize) {
                return false;
            }
            return this.elementWeight > this.targetWeightDisplay;
        },
        targetWeightDisplay() {
            return Math.round(this.targetWeight * 10000) / 100;
        },
        elementWeight() {
            if (!this.totalPortfolioSize) {
                return null;
            }
            return (
                Math.round((this.value.value / this.totalPortfolioSize) * 10000) / 100
            );
        },
    },
};
</script>
