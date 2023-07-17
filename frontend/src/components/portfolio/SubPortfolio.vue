<template>
    <v-list-item>
        <template v-slot:prepend>
            <ProviderIcon :iconType="portfolio.provider" />
        </template>
        <v-list-item-title>{{ portfolio.name }}</v-list-item-title>
<span><CurrencyItemVue :loading="portfolio.loading" :value="{ currency: '$', value: portfolioSum }" /> in {{ portfolioLength }} stocks</span>
        <v-spacer></v-spacer>
        <span class="text-medium-emphasis" ><CurrencyItemVue :loading="portfolio.loading" :value="portfolio.cash"/> cash</span>
        <template v-slot:append>
            <v-spacer/>
            <ProviderLoginPopup stateful :provider="portfolio.provider" :portfolioName ="parentName" ></ProviderLoginPopup>
            <!-- <v-btn v-if="loggedIn" color="green" icon="mdi-check" variant="text"></v-btn> -->
            <!-- <v-btn v-else color="grey-lighten-1" icon="mdi-login" variant="text"></v-btn> -->
            <v-spacer>
            </v-spacer>
            <v-btn v-if="loggedIn" color="red" prependIcon="mdi-cancel" variant="text">
                Remove
            </v-btn>
        </template>
    </v-list-item>
</template>

<script>
import CurrencyItem from '../generic/CurrencyItem.vue';
import ProviderIcon from '../icons/ProviderIcon.vue';
import ProviderLoginPopup from "@/components/portfolio/ProviderLoginPopup.vue";
export default {
    data() {
        return {
            loggedIn: true
        }
    },
    components: {
        CurrencyItemVue: CurrencyItem,
        ProviderIcon: ProviderIcon,
        ProviderLoginPopup: ProviderLoginPopup
    },

    props: {
        parentName: {
            type: String,
            required: false,
            default: ''
        },
        portfolio: {
            type: Object,
            required: true
        }
    },
    computed: {
        portfolioSum() {
            return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value,0);
        },
        portfolioLength() {
            return this.portfolio.holdings.length;
        },
    }
}
</script>