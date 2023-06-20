<template>
    <v-card>
        <v-card-title class="d-flex justify-center align-center">Customize Index</v-card-title>
        <v-card-actions class="d-flex justify-center align-center">
            <v-btn class="text-none" variant="outlined" @click="saveDefaultModifications()">
                Save as Default
            </v-btn>
            <TailorStockPopup />
            <TailorListPopup />
            <v-btn class="text-none" variant="outlined" color="red" @click="clearAllModifications()">
                Clear All
            </v-btn>
        </v-card-actions>
        <v-card-text>
            <v-card>
                <v-card-title>Excluded Stocks</v-card-title>
                <v-card-text>
                    <template v-for="element in excludedTickers" :key="element">
                        <v-list-item>{{ element }}
                            <template v-slot:append>
                                <v-tooltip>
                                    <template v-slot:activator="{ props }">
                                        <v-btn v-bind="props" @click="removeStockExclusion(element)" icon density="compact">
                                            <v-icon  color="warning">mdi-cancel</v-icon>
                                        </v-btn>
                                    </template>
                                    <span>Remove Exclusion</span>
                                </v-tooltip>
                            </template>
                        </v-list-item>
                    </template>
                </v-card-text>
            </v-card>
            <v-card>
                <v-card-title>Excluded Lists</v-card-title>
                <v-card-text>
                    <template v-for="element in excludedLists" :key="element">
                        <v-list-item>{{ element }}
                            <v-chip-group active-class="primary">
                                <v-chip v-for="tag in stockLists[element]" :key="tag" :value="tag" label>
                                    {{ tag }}
                                </v-chip>
                            </v-chip-group>
                            <template v-slot:append>
                                <v-tooltip>
                                    <template v-slot:activator="{ props }">
                                        <v-btn v-bind="props" @click="removeListExclusion(element)" icon density="compact">
                                            <v-icon  color="warning">mdi-cancel</v-icon>
                                        </v-btn>
                                    </template>
                                    <span>Remove Exclusion</span>
                                </v-tooltip>
                            </template>
                        </v-list-item>
                    </template>
                    <!-- <template v-for="element in excludedLists" :key="element">
                    <div>{{ element }}</div>
                </template> -->
                </v-card-text>
            </v-card>
            <v-card>
                <v-card-title>Reweighted Stocks</v-card-title>
                <v-card-text>
                    <template v-for="element in stockModifications" :key="element.ticker">
                        <v-list-item>{{ element.ticker }} ({{ element.scale }}%)
                            <template v-slot:append>
                                <v-tooltip>
                                    <template v-slot:activator="{ props }">
                                        <v-btn v-bind="props" @click="removeStockModification(element.ticker)" icon
                                            density="compact">
                                            <v-icon  color="warning">mdi-cancel</v-icon>
                                        </v-btn>
                                    </template>
                                    <span>Remove All Modifications</span>
                                </v-tooltip>
                            </template>
                        </v-list-item>
                    </template>
                </v-card-text>
            </v-card>

            <v-card>
                <v-card-title>Reweighted Lists</v-card-title>
                <v-card-text>
                    <template v-for="element in listModifications" :key="element">
                        <div>{{ element }}</div>
                    </template>
                </v-card-text>
            </v-card>
        </v-card-text>
    </v-card>
</template>

<script>
import {
    mapActions,
    mapGetters
} from 'vuex';

import TailorStockPopup from './TailorStockPopup.vue';
import TailorListPopup from './TailorListPopup.vue';

export default {
    name: "TailorComponent",
    components: {
        TailorStockPopup,
        TailorListPopup
    },
    data() {
        return {

        }
    },
    computed: {
        ...mapGetters(['excludedTickers', 'excludedLists', 'stockModifications', 'listModifications', 'stockLists'])
    },
    methods: {
        ...mapActions(['excludeStock', 'removeStockExclusion', 'removeStockModification', 'removeListExclusion', 'removeListModification',
            'saveDefaultModifications']),
    },
    props: {},

};
</script>
