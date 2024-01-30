<template>
    <v-card title="Index Settings" theme="dark" class="pb-4">
        <v-card-text>
            <p class="pa-4">
                Select the base index to use for your portfolio.</p>
            <v-select v-model="list" :items="indexKeys"
            @update:modelValue="handlePortfolioTargetInput"
             density="compact" variant="solo" label="Base Index"></v-select>
            <v-chip-group active-class="primary">
                <v-chip v-for="tag in listMembers" :key="tag" :value="tag" label>
                    {{ tag }}
                </v-chip>
            </v-chip-group>
            <v-divider />
            <v-text-field class="input-field" variant="solo" @input="handlePortfolioSizeInput" label="Target Portfolio Size"
                v-model="portfolioTarget" :rules="numberValidationRules">
            </v-text-field>
            <!-- <v-text-field v-model="minWeight" :disabled="excluded" :rules="numberValidationRules" color="blue-darken-4" label="Minimum Weighting" density="compact" variant="solo" hide-details inline inset></v-text-field> -->
        </v-card-text>
    </v-card>
</template>


   
<script lang="ts">
import {
    mapActions,
    mapGetters
} from 'vuex'


import { debounce } from 'lodash';


export default {
    name: "TailorListPopup",
    data: () => ({
        list: '',
        stockLists: {},
        excluded: false,
        dialog: false,
        weight: 100,
        minWeight: 0,
        portfolioTarget: 100_000
    }),
    props: {
        portfolioName: {
            type: String,
            required: true,
        },
    },
    computed: {
        ...mapGetters(['portfolioTarget', 'indexes','portfolioCustomization',]),
        listMembers() {
            return this.stockLists[this.list]
        },
        indexKeys() {
            return Object.keys(this.indexes)
        },
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
        mutations() {
            return this.customizations.stockModifications.length + this.customizations.listModifications.length + this.customizations.excludedLists.size + this.customizations.excludedTickers.size
        },
        customizations() {
            return this.portfolioCustomization

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
        ...mapActions(['setPortfolioSize', 'setPortfolioTargetIndex']),
        handlePortfolioSizeInput: debounce(function () {
            // Code to execute after the debounce delay
            this.setPortfolioSize({ portfolioName: this.portfolioName, size: Number(this.portfolioTarget) })
        }, 300), // Debounce delay in milliseconds
        handlePortfolioTargetInput(index) {
            this.setPortfolioTargetIndex({index:index})
        },
        submit() {
            // if (this.excluded) {
            //     this.excludeList({portfolioName:this.portfolioName, list:this.list});
            // } else {
            //     this.modifyList({
            //         'portfolioName': this.portfolioName,
            //         'list': this.list,
            //         'scale': this.weight / 100,
            //         // 'minWeight': this.minWeight
            //     })
            // }
            // this.dialog = false;
        }
    },
}
</script>