<template>
  <v-card title="Index Settings" class="pb-4 sharp">
    <v-card-text>
      <p class="pa-4">Select the base index to use for your portfolio.
An index is a collection of stocks and assigned weights which usually tracks the entire market or a subset of the market. 
Total Market is a common index used by VTI and other familiar 'index funds' and can be a good place to start.</p>
      <v-select
        v-model="list"
        :items="indexKeys"
        @update:modelValue="handlePortfolioTargetInput"
        density="compact"
        variant="solo"
        label="Base Index"
        :disabled="pythonLoading"
        :class="{ 'glowing-border': highlight}"
      ></v-select>
      <v-chip-group active-class="primary">
        <v-chip v-for="tag in listMembers" :key="tag" :value="tag" label>
          {{ tag }}
        </v-chip>
      </v-chip-group>
      <v-divider />
      <v-text-field
        class="input-field"
        variant="solo"
        @input="handlePortfolioSizeInput"
        label="Target Portfolio Size"
        v-model="portfolioTargetLocal"
        :rules="numberValidationRules"
        :disabled="pythonLoading"
      >
      </v-text-field>
      <!-- <v-text-field v-model="minWeight" :disabled="excluded" :rules="numberValidationRules" color="blue-darken-4" label="Minimum Weighting" density="compact" variant="solo" hide-details inline inset></v-text-field> -->
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { mapActions, mapGetters } from "vuex";

// @ts-ignore
import pkg from "lodash";
const { debounce } = pkg;

export default {
  name: "ConfigureIndex",
  data: () => ({
    list: "",
    stockLists: {},
    excluded: false,
    dialog: false,
    weight: 100,
    minWeight: 0,
    portfolioTargetLocal: 100_000,
  }),
  props: {
    highlight: {
    type: Boolean,
    default: false,}
   },
  computed: {
    ...mapGetters(["portfolioTarget", "indexes", "portfolioCustomization", "pythonLoading"]),
    listMembers() {
      return this.stockLists[this.list];
    },
    indexKeys() {
      return Object.keys(this.indexes).sort();
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
          return "Only numbers are allowed.";
        },
      ];
    },
    mutations() {
      return (
        this.customizations.stockModifications.length +
        this.customizations.listModifications.length +
        this.customizations.excludedLists.size +
        this.customizations.excludedTickers.size
      );
    },
    customizations() {
      return this.portfolioCustomization;
    },
    excludedTickers() {
      return this.customizations.excludedTickers;
    },
    excludedLists() {
      return this.customizations.excludedLists;
    },
    stockModifications() {
      return this.customizations.stockModifications;
    },
    listModifications() {
      return this.customizations.listModifications;
    },
  },
  methods: {
    ...mapActions(["setPortfolioSize", "setPortfolioTargetIndex"]),
    handlePortfolioSizeInput: debounce(function () {
      // Code to execute after the debounce delay
      this.setPortfolioSize({
        portfolioName: this.portfolioName,
        size: Number(this.portfolioTargetLocal),
      });
    }, 300), // Debounce delay in milliseconds
    handlePortfolioTargetInput(index) {
      this.setPortfolioTargetIndex({ index: index });
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
    },
  },
};
</script>
<style>
.glowing-border {
    /* border: 2px solid #dadada; */
    /* border-radius: 7px; */
    outline: none;
    border-color: #9ecaed;
    box-shadow: 0 0 0 0 rgba(52, 172, 224, 1);
    animation: pulse-blue 2s infinite;
}

@keyframes pulse-blue {
	0% {
		transform: scale(0.95);
		box-shadow: 0 0 0 0 rgba(52, 172, 224, 0.7);
	}
	
	70% {
		transform: scale(1);
		box-shadow: 0 0 0 10px rgba(52, 172, 224, 0);
	}
	
	100% {
		transform: scale(0.95);
		box-shadow: 0 0 0 0 rgba(52, 172, 224, 0);
	}
}
</style>