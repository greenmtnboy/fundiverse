<template>
    <v-dialog v-model="visible" fullscreen hide-overlay :scrim="false">
        <template v-slot:activator="{ props }">
            <v-badge v-if="mutations" :content="mutations">
                <v-btn @click="visible = !visible" v-on="props">Customize</v-btn>
            </v-badge>
            <v-btn @click="visible = !visible" v-on="props" v-else>Customize</v-btn>
        </template>
        <v-card>
            <v-toolbar dark color="primary">
                <!-- <v-btn
            icon
            dark
            @click="visible= false"
          >
            <v-icon>mdi-close</v-icon> -->
                <!-- </v-btn> -->
                <v-toolbar-title>Customizations for {{ portfolioName }}</v-toolbar-title>
                <v-spacer></v-spacer>
                <v-toolbar-items>
                    <v-btn variant="text" @click="visible = false">
                        Close
                    </v-btn>
                </v-toolbar-items>
            </v-toolbar>
            <!-- <v-card-title class="d-flex justify-center align-center">Customize Index</v-card-title> -->
            <v-card-actions class="d-flex justify-center align-center">
                <v-btn min-width="132" v-if="showSaveSuccess" class="text-none" variant="outlined">
                    <v-icon>mdi-check</v-icon>
                </v-btn>
                <!-- <v-btn v-else :loading="isSaving" class="text-none" variant="outlined"
                    @click="saveCustomizations()">
                    Save as Default
                </v-btn>
                <v-btn :loading="isSaving" class="text-none" variant="outlined"
                    @click="loadCustomizations()">
                    Load Saved
                </v-btn> -->
                <TailorStockPopup :portfolioName="portfolioName" />
                <TailorListPopup :portfolioName="portfolioName" />
                <v-btn min-width="132" v-if="showClearSuccess" class="text-none" variant="outlined">
                    <v-icon>mdi-check</v-icon>
                </v-btn>
                <v-btn v-else :loading="isClearing" class="text-none" variant="outlined" color="red"
                    @click="clearAllModificationsLocal()">
                    Clear All
                </v-btn>
            </v-card-actions>
            <v-card-text>
                <v-card rounded="0">
                    <v-card-title>Excluded Stocks
                        <IconTooltip
                            text="Excluded stocks will be removed from the index, and the index is then recomputed to have all weights sum to 100" />
                    </v-card-title>
                    <v-card-text>
                        <template v-for="ticker in excludedTickers" :key="ticker">
                            <TailorStockListItem :ticker="ticker" :portfolioName="portfolioName" />
                        </template>
                    </v-card-text>
                </v-card>
                <v-card rounded="0">
                    <v-card-title>Excluded Lists
                        <IconTooltip
                            text="Excluded lists have all components stocks removed from the index, and the index is then recomputed to have all weights sum to 100%" />
                    </v-card-title>
                    <v-card-text>
                        <template v-for="element in excludedLists" :key="element">
                            <TailorComponentListItem :list="element" />
                        </template>
                    </v-card-text>
                </v-card>
                <v-card rounded="0">
                    <v-card-title>Reweighted Stocks
                        <IconTooltip
                            text="Reweighted stocks have their % in the index multipled by this factor, and the index is then reweighted to 100%. This means that 200% of a 3% stock does not result in a weight of 6%; it results in about 5.8%" />
                    </v-card-title>
                    <v-card-text>
                        <template v-for="element in stockModifications" :key="element.ticker">
                            <TailorStockListItem mode="modification" :portfolioName="portfolioName" :ticker="element.ticker" :scale="element.scale" />
                        </template>
                    </v-card-text>
                </v-card>

                <v-card rounded="0">
                    <v-card-title>Reweighted Lists
                        <IconTooltip
                            text="Reweighted lists have the % of every component stock in the index multipled by this factor, and the index is then reweighted to 100%. This means that 200% of a 3% stock does not result in a weight of 6%; it results in about 5.8%" />
                    </v-card-title>
                    <v-card-text>
                        <template v-for="element in listModifications" :key="element">
                            <TailorComponentListItem :list="element.list" :weight="element.scale" />
                        </template>
                    </v-card-text>
                </v-card>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>


<style>
/* Custom styles to make the dialog full page */
.v-dialog--fullscreen {
    width: 100%;
    height: 100%;
    max-width: none;
    max-height: none;
    margin: 0;
}

.v-dialog--fullscreen .v-dialog__content {
    height: 100%;
}
</style>
<script>
import {
    mapActions,
    mapGetters
} from 'vuex';

import TailorStockPopup from './TailorStockPopup.vue';
import TailorListPopup from './TailorListPopup.vue';
import TailorComponentListItem from './TailorComponentListItem.vue';
import TailorStockListItem from './TailorStockListItem.vue';
import IconTooltip from '../generic/IconTooltip.vue'
import PortfolioCustomization from '@/models/PortfolioCustomization';
export default {
    name: "TailorComponent",
    components: {
        TailorStockPopup,
        TailorListPopup,
        TailorComponentListItem,
        TailorStockListItem,
        IconTooltip
    },
    data() {
        return {
            showSaveSuccess: false,
            isSaving: false,
            isClearing: false,
            showClearSuccess: false,
            visible: false
        }
    },
    computed: {
        ...mapGetters(['portfolioCustomizations', 'stockLists']),
        mutations() {
            return this.customizations.stockModifications.length + this.customizations.listModifications.length + this.customizations.excludedLists.size + this.customizations.excludedTickers.size
        },
        customizations() {
            const customizations = this.portfolioCustomizations.get(this.portfolioName)
            if (customizations) { return customizations }
            return new PortfolioCustomization({
                reweightIndex: true,
                indexPortfolio: null,
                excludedLists: new Set(), excludedTickers: new Set(),
                stockModifications: [], listModifications: []
            })
        },
        excludedTickers() {
            return this.customizations.excludedTickers
        },
        excludedLists() {
            return this.customizations.excludedLists
        },
        stockModifications() {
            return this.customizations.stockModifications
        },
        listModifications() {
            return this.customizations.listModifications
        },
    },
    methods: {
        ...mapActions(['clearAllModifications',
            'removeStockExclusion', 'removeStockModification',
            'removeListExclusion', 'removeListModification',
            'saveCustomizations', 'loadCustomizations',
            'saveDefaultModifications']),
        saveDefaultModificationsLocal() {
            this.isSaving = true;
            setTimeout(() => {
                this.saveDefaultModifications({ portfolioName: this.portfolioName }).then(() => {
                    this.showSaveSuccess = true;
                    // Reset the success state after a delay
                    setTimeout(() => {
                        this.showSaveSuccess = false;
                    }, 2000);
                }).finally(() => {
                    this.isSaving = false;
                })
            }, 600);
        },
        clearAllModificationsLocal() {
            this.isClearing = true;
            this.clearAllModifications({ portfolioName: this.portfolioName }).then(() => {
                this.showClearSuccess = true;
                // Reset the success state after a delay
                setTimeout(() => {
                    this.showClearSuccess = false;
                }, 2000);
            }).finally(() => {
                this.isClearing = false;
            })
        }
    },
    props: {
        portfolioName: {
            type: String,
            required: true
        }
    },

};
</script>
