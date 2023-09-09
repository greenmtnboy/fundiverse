<template>
    <!-- rounded="0" -->
    <v-dialog v-model="dialog" max-width="500">
        <template v-slot:activator="{ props }">
            <v-btn class="text-none" color="primary" variant="outlined" v-bind="props">
                Add List Adjustment
            </v-btn>
        </template>

        <v-card title="Stock Settings">
            <v-card-text>
                <p class="pb-4">
                    You can exclude a list of stocks entirely with the below toggle, or scale the weighting of all stocks in
                    the list in the index by some percent. The default 100% would not change the weight in the index.
                </p>
                <v-select v-model="list" :items="indexKeys" density="compact" variant="solo" label="Stock List"></v-select>
                <v-chip-group active-class="primary">
                    <v-chip v-for="tag in listMembers" :key="tag" :value="tag" label>
                        {{ tag }}
                    </v-chip>
                </v-chip-group>
                <v-divider />
                <v-switch v-model="excluded" :label="excluded ? 'Exclude' : 'Keep'" color="blue-darken-4" density="compact"
                    hide-details inline inset></v-switch>
                <v-text-field v-model="weight" :disabled="excluded" label="Weighting %" variant="solo" color="blue-darken-4"
                    density="compact" :rules="numberValidationRules" hide-details inline inset></v-text-field>
                <!-- <v-text-field v-model="minWeight" :disabled="excluded" :rules="numberValidationRules" color="blue-darken-4" label="Minimum Weighting" density="compact" variant="solo" hide-details inline inset></v-text-field> -->
            </v-card-text>
            <v-divider></v-divider>

            <v-card-actions class="justify-center px-6 py-3">
                <v-btn class="flex-grow-1 text-none" variant="plain" @click="dialog = false">
                    Exit
                </v-btn>

                <v-btn :disabled="!hasValidChanges" class="text-white flex-grow-1 text-none" color="primary" variant="flat"
                    @click="submit()">
                    Save
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
    
<script lang="ts">
import {
    mapActions,
    mapGetters
} from 'vuex'
export default {
    name: "TailorListPopup",
    data: () => ({
        list: '',
        excluded: false,
        dialog: false,
        weight: 100,
        minWeight: 0,
    }),
    props: {
        portfolioName: {
            type: String,
            required: true,
        },
    },
    mounted() {
        this.getStockLists()
    },
    computed: {
        ...mapGetters(['stockLists']),
        listMembers() {
            return this.stockLists[this.list]
        },
        indexKeys() {

            return Object.keys(this.stockLists)
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
    },
    methods: {
        ...mapActions(['excludeList', 'modifyList', 'getStockLists']),

        submit() {
            if (this.excluded) {
                this.excludeList({portfolioName:this.portfolioName, list:this.list});
            } else {
                this.modifyList({
                    'portfolioName': this.portfolioName,
                    'list': this.list,
                    'scale': this.weight / 100,
                    // 'minWeight': this.minWeight
                })
            }
            this.dialog = false;
        }
    },
}
</script>
