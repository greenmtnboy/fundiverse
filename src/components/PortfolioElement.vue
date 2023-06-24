<template>
    <v-list-item :min-height="15">
        <div>{{ element.ticker }}
            <p class="text-medium-emphasis">{{ element.value.currency }}{{ element.value.value }} ({{
                elementWeight }}%)</p>
        </div>
        <template v-slot:append>
            <v-tooltip v-if="element.unsettled">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon density="compact">
                        <v-icon color="warning">mdi-exclamation</v-icon>
                    </v-btn>
                </template>
                <span>This stock has unsettled orders and will be skipped for now</span>
            </v-tooltip>
            <v-btn v-else icon density="compact">
            </v-btn>

        </template>
    </v-list-item>
</template>

<script>
import PortfolioElementModel from '../models/PortfolioElementModel';

export default {
    name: "PortfolioElement",
    data() {
        return {
            loading: false
        }
    },
    props: {
        element: {
            type: PortfolioElementModel,
            required: true
        },
        totalPortfolioSize: {
            type: Number,
            required: false
        },
    },
    computed: {
        elementWeight() {
            if (!this.totalPortfolioSize) {
                return null;
            }
            return Math.round((this.element.value.value / this.totalPortfolioSize) * 10000) / 100;
        },
    }
};
</script>
