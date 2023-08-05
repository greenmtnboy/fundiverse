<template>
    <v-list-item>
        <v-list-item-title><span class="px-1">{{ ticker }}</span>
            <v-chip :color="weight >= 1 ? 'green' : 'red'" v-if="weight" small outlined>{{ weight * 100 }}%</v-chip>
        </v-list-item-title>
        <template v-slot:append>
            <v-tooltip>
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" @click="localRemoveStockExclusion(ticker)" icon density="compact">
                        <v-icon color="warning">mdi-cancel</v-icon>
                    </v-btn>
                </template>
                <span>Remove Exclusion</span>
            </v-tooltip>
        </template>
    </v-list-item>
</template>

<script>
import {
    mapActions,
} from 'vuex';

export default {
    name: "TailorComponentStockItem",
    data() {
        return {
        };
    },
    props: {
        ticker: {
            type: String,
            required: true
        },
        weight: {
            type: Number,
            required: false
        },
        portfolioName: {
            type: String,
            required: true
        }
    },
    computed: {
    },
    methods: {
        ...mapActions(['removeStockExclusion']),
        localRemoveStockExclusion(data) {
            this.removeStockExclusion({portfolioName:this.portfolioName,ticker:data})
        },
    },
};
</script>
