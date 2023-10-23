<template>
    <v-list-item>
        <v-chip :color="element.status === 'placed' ? 'green' : 'red'" small outlined>{{
            element.status }}</v-chip>
        <CurrencyItem :value="element.value" /> of
        <TickerDisplay :ticker="element.ticker" /> on {{ element.provider
        }}
        <template v-slot:append v-if="element.message">
            <v-tooltip>
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" icon density="compact">
                        <v-icon color="warning">mdi-exclamation</v-icon>
                    </v-btn>
                </template>
                <span>{{ element.message }}</span>
            </v-tooltip>
        </template>

    </v-list-item>
</template>

<script lang="ts">
import CurrencyItem from '../generic/CurrencyItem.vue'
import TickerDisplay from '../generic/TickerDisplay.vue'
export default {
    name: "TailorComponentStockItem",
    data() {
        return {
        };
    },
    components: { TickerDisplay, CurrencyItem },
    props: {
        element: {
            type: Object,
            required: true
        },
    },
    computed: {
    },
    methods: {
    },
};
</script>
