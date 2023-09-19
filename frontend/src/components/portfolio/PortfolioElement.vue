<template>
    <v-list-item :min-height="15">
        <div>
            <TickerDisplay :ticker="ticker" />
            <p class="text-medium-emphasis">
                <CurrencyItem :value="value"></CurrencyItem> ({{
                    elementWeight }}%)
            </p>
        </div>
        <template v-slot:append>
            <v-tooltip v-if="unsettled">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon density="compact">
                        <v-icon color="warning">mdi-exclamation</v-icon>
                    </v-btn>
                </template>
                <span>This stock has unsettled orders</span>
            </v-tooltip>
            <v-btn v-else-if="!this.targetWeight" icon density="compact">
            </v-btn>
            <v-tooltip v-else-if="onGoal">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon density="compact">
                        <v-icon color="success">mdi-check</v-icon>
                    </v-btn>
                </template>
                <span>This stock is near goal ({{ targetWeightDisplay }}%)</span>
            </v-tooltip>
            <v-tooltip v-else-if="overGoal">
                <template v-slot:activator="{ props }">
                    <v-btn color="blue" v-bind="props" icon density="compact">
                        <v-icon>mdi-arrow-up</v-icon>
                    </v-btn>
                </template>
                <span>This stock is over goal ({{ targetWeightDisplay }}%)</span>
            </v-tooltip>
            <v-tooltip v-else>
                <template v-slot:activator="{ props }">
                    <v-btn color="orange" v-bind="props" icon density="compact">
                        <v-icon>mdi-arrow-down</v-icon>
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
import CurrencyItem from '../generic/CurrencyItem.vue';
import TickerDisplay from '../generic/TickerDisplay.vue';
const comparisonThreshold = .1;

export default {
    name: "PortfolioElement",
    data() {
        return {
            loading: false
        }
    },
    components: {
        CurrencyItem,
        TickerDisplay
    },
    props: {
        ticker: {
            type: String,
            required: true
        },
        value: {
            type: Object,
            required: true
        },
        targetWeight: {
            type: Number,
            required: false
        },
        totalPortfolioSize: {
            type: Number,
            required: false
        },
        unsettled: {
            type: Boolean,
            required: false
        }
    },
    computed: {
        onGoal() {
            if (!this.totalPortfolioSize) {
                return false;
            }
            return Math.abs(this.elementWeight - this.targetWeightDisplay) < comparisonThreshold;
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
            return Math.round((this.value.value / this.totalPortfolioSize) * 10000) / 100;
        },
    }
};
</script>
