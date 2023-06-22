<template>
    <v-dialog v-model="visible" fullscreen hide-overlay :scrim="false">
        <template v-slot:activator="{ on }">
            <v-badge v-if="mutations" :content="mutations">
                <v-btn @click="visible = !visible" v-on="on">Customize</v-btn>
            </v-badge>
            <v-btn @click="visible = !visible" v-on="on" v-else>Customize</v-btn>
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
                <v-toolbar-title>Customizations</v-toolbar-title>
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
                <v-btn v-else :loading="isSaving" class="text-none" variant="outlined"
                    @click="saveDefaultModificationsLocal()">
                    Save as Default
                </v-btn>
                <TailorStockPopup />
                <TailorListPopup />
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
                        <template v-for="element in excludedTickers" :key="element">
                            <TailorStockListItem :ticker="element" />
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
                            <TailorStockListItem :ticker="element" :weight="element.scale" />
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
import TailorComponentListItem from './tailor/TailorComponentListItem.vue';
import TailorStockListItem from './tailor/TailorStockListItem.vue';
import IconTooltip from './generic/IconTooltip.vue'
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
        ...mapGetters(['excludedTickers', 'excludedLists', 'stockModifications', 'listModifications', 'stockLists']),
        mutations() {
            return this.$store.getters.totalModifications
        },
    },
    methods: {
        ...mapActions(['excludeStock', 'clearAllModifications', 'removeStockExclusion', 'removeStockModification', 'removeListExclusion', 'removeListModification',
            'saveDefaultModifications']),
        saveDefaultModificationsLocal() {
            this.isSaving = true;
            setTimeout(() => {
                this.saveDefaultModifications().then(() => {
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
            this.clearAllModifications().then(() => {
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
    },

};
</script>
