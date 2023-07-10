<template>
    <!-- rounded="0" -->
    <v-dialog v-model="dialog" max-width="500">
        <template v-slot:activator="{ props }">
            <v-btn :disabled="!selectedIndex" @click="planPurchase()" min-width="200px" class="d-flex flex-column"
                color="primary" variant="outlined" v-bind="props">
                Buy ({{ cash.currency }}{{ Math.round(cash.value) }} Available)
            </v-btn>
            <!-- <v-btn :disabled="!selectedIndex" class="d-flex flex-column" > -->
            <!-- </v-btn> -->
        </template>

        <v-card :title="`Confirm $${toPurchase} Purchase`">
            <v-card-text>
                <p>
                    Review the list of planned transactions and click confirm to submit.
                    The default purchase order will go largest first, but you can select alternative options.</p>
   
                    <v-row > <v-col width=12 justify="center" align="center"><v-chip-group v-model="selectedMode" mandatory selected-class="text-primary"
                                @update:modelValue="newValue => planPurchase()">
                                <v-chip v-for="mode in modes" :key="mode.id" :value="mode.id" :label="true"
                                    :item-text="mode.name">
                                    {{ mode.name }}
                                </v-chip>
                            </v-chip-group>
                        </v-col>
                    </v-row>
                    <v-row>
                        <v-col cols=12>
                            <v-text-field class="input-field" variant="solo" label="Purchase Amount"
                                v-model="toPurchaseInternal" :rules="numberValidationRules"
                                @update:modelValue="newValue => handleOrderSizeInput()">
                            </v-text-field>
                        </v-col>
                    </v-row>
                    <v-row class="py-5" height="15" v-if="initialLoading">
                        <v-progress-linear height="10" indeterminate color="primary"></v-progress-linear>

                    </v-row>
                    <v-row v-else>
                        <v-col cols=12>
                            <template v-for="element in plan.to_buy" :key="element.ticker">

                                <v-list-item> <v-chip :color="element.order_type === 'BUY' ? 'green' : 'red'" small
                                        outlined>{{
                                            element.order_type }}</v-chip>
                                    <CurrencyItem :value="element.value" /> of {{ element.ticker }}
                                    <template v-slot:append>
                                        <v-tooltip>
                                            <template v-slot:activator="{ props }">
                                                <v-btn v-bind="props" @click="removeOrder(element.ticker)" icon
                                                    density="compact">
                                                    <v-icon color="warning">mdi-cancel</v-icon>
                                                </v-btn>
                                            </template>
                                            <span>Remove Order</span>
                                        </v-tooltip>
                                    </template>
                                </v-list-item>
                            </template>
                        </v-col>
                    </v-row>

            </v-card-text>

            <v-divider></v-divider>
            <v-alert :min-height="200" v-model="alertVisible" type="error" closable @input="alertVisible = false">
                {{ exception }}
            </v-alert>
            <v-card-actions class="justify-center px-6 py-3">
                <v-btn class="flex-grow-1 text-none" variant="plain" @click="dialog = false">
                    Exit
                </v-btn>

                <v-btn :disabled="initialLoading" :loading="loading" class="text-white flex-grow-1 text-none"
                    color="primary" variant="flat" @click="submit()">
                    Submit Orders
                </v-btn>

            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
    
<script>
import {
    mapActions,
} from 'vuex'

import instance from '../../api/instance'
import exceptions from '../../api/exceptions'
import CurrencyItem from '../generic/CurrencyItem.vue'

import {
    debounce
} from 'lodash';
function roundToNearestTen(number) {
    return Math.floor(number / 10) * 10;
}

export default {
    name: "ConfirmPurchase",
    data: () => ({
        plan: { 'to_buy': [], 'to_sell': [] },
        exception: null,
        alertVisible: false,
        dialog: false,
        loading: false,
        initialLoading: true,
        toPurchaseInternal: 50,
        toPurchase: 50,
        selectedMode: 2,
        modes: [{ name: 'Cheapest First', id: 1 },
        { name: 'Largest Diff First', id: 2 },
        { name: 'Equal Spread', id: 3 },
        ]
    }),
    components: {
        CurrencyItem
    },
    props: {
        targetSize: {
            type: Number,
            required: true
        },
        refreshCallback: {
            type: Function,
            required: true
        },
        selectedIndex: {
            type: String,
            required: false
        },
        cash: {
            type: Object,
            required: true
        },
        disabled: {
            type: Boolean,
            required: false,
            default: false
        }
    },

    computed: {
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
    mounted() {
        let defaultPurchase = roundToNearestTen(this.cash.value * .9);
        if (defaultPurchase < 1) {
            defaultPurchase = 10;
        }
        this.toPurchase = defaultPurchase;
        this.toPurchaseInternal = defaultPurchase;
    },
    methods: {
        ...mapActions(['excludeList', 'modifyList']),
        handleOrderSizeInput: debounce(function () {
            // Code to execute after the debounce delay
            this.toPurchase = Number(this.toPurchaseInternal)
            this.planPurchase()
        }, 300), // Debounce delay in milliseconds
        removeOrder(ticker) {
            this.plan['to_buy'] = this.plan['to_buy'].filter((element) => element.ticker !== ticker)
        },
        planPurchase() {
            this.initialLoading = true;
            return instance.post('http://localhost:3000/plan_purchase', {
                'to_purchase': this.toPurchase,
                'target_size': this.targetSize,
                'index': this.selectedIndex,
                'stock_exclusions': Array.from(this.$store.getters.excludedTickers),
                'list_exclusions': Array.from(this.$store.getters.excludedLists),
                'stock_modifications': this.$store.getters.stockModifications,
                'list_modifications': this.$store.getters.listModifications,
                'purchase_strategy': this.selectedMode,
            }
            ).then((response) => {
                this.plan = response.data
            }).catch((error) => {
                if (error instanceof exceptions.auth) {
                    // Handle the custom exception
                    console.log('Authentication error, redirecting')
                } else {
                    throw error
                }
            }).finally(() => {
                this.initialLoading = false;
            });
        },
        submit() {
            this.loading = true;
            this.alertVisible = false;
            return instance.post('http://localhost:3000/buy_index_from_plan', {
                'plan': this.plan
            }
            ).then(() => {
                this.plan = { 'to_buy': [], 'to_sell': [] }
                this.refreshCallback()
                this.dialog = false;
            }).catch((exception) => {
                if (exception instanceof exceptions.auth) {
                    // Handle the custom exception
                    console.log('Authentication error, redirecting')
                    return
                }
                this.alertVisible = true;
                if (exception.response) {
                    this.exception = exception.response.data;
                }
                else {
                    this.exception = exception;
                }
            }).finally(() => {
                this.loading = false;

            });

        }
    },
}
</script>
