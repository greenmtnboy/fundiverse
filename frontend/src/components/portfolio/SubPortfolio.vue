<template>
    <v-list-item>
        <v-list-item-title>{{ portfolio.name }}</v-list-item-title>
        <CurrencyItemVue :value="{currency:'$', value:portfolioSum}"/>

        <template v-slot:append>
 
          <v-btn v-if="loggedIn"
            color="green"
            icon="mdi-check"
            variant="text"
          ></v-btn>
          <v-btn v-else
            color="grey-lighten-1"
            icon="mdi-login"
            variant="text"
          ></v-btn>
          <v-spacer>

          </v-spacer>
          <v-btn v-if="loggedIn"
            color="red"
            icon="mdi-cancel"
            variant="text"
          ></v-btn>
        </template>
    </v-list-item>
</template>

<script>
import CurrencyItem from '../generic/CurrencyItem.vue';
export default {
    data() {
        return {
            loggedIn: true
        }
    },
    components: {
        CurrencyItemVue: CurrencyItem
    },
    props: {
        portfolio: {
            type: Object,
            required: true
        }
    },
    computed: {
        portfolioSum() {
            return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
        },
    }
}
</script>