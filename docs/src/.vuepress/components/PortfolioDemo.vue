<template>
    <CompositePortfolioView :portfolio="staticDemoPortfolio"></CompositePortfolioView>
    <v-row no-gutters>
        <v-col col=6>
            <PortfolioView :portfolio="staticDemoPortfolio" :targetSize="portfolioTarget"></PortfolioView>
        </v-col>
        <v-col col=6>
            <TargetPortfolioViewStatic :portfolio="staticDemoTargetPortfolio" :targetSize="portfolioTarget">
            </TargetPortfolioViewStatic>
        </v-col>
    </v-row>



</template>
<style>
.sharp {
    border-radius: 0;
}
</style>
<script lang="ts">
import CompositePortfolioView from './portfolio/CompositePortfolio.vue'
import TargetPortfolioViewStatic from "./target_portfolio/TargetPortfolioViewStatic.vue";
import PortfolioView from "./portfolio/PortfolioView.vue"
import StockListSetter from "./target_portfolio/StockListSetter.vue";
import IndexSetter from "./target_portfolio/IndexSetter.vue";
import StockSetter from "./target_portfolio/StockSetter.vue";
import { mapGetters, mapActions } from "vuex";

export default {
    components: {
        TargetPortfolioViewStatic,
        StockListSetter,
        IndexSetter,
        StockSetter,
        CompositePortfolioView,
        PortfolioView,
    },
    data() {
        return {
            activeSelector: "index",
        };
    },
    methods: {
        ...mapActions(["getStockLists", "getIndexes", "getPython"]),
    },
    computed: {
        ...mapGetters([
            "staticDemoPortfolio",
            "staticDemoTargetPortfolio",
            "indexesLoading",
            "pythonLoading",
        ]),
        portfolioTarget() {
            return this.staticDemoPortfolio.target_size;
        }
    },
    mounted() {
    },
};
</script>