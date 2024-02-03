<template>
  <v-card title="List Settings" theme="dark" class="pb-4">
    <v-card-text>
      <p class="pa-4">
        You can custom the portfolio by excluding or adjusting the weight of
        premade lists of stocks.
      </p>
      <p class="pa-4">
        Select your list in the dropdown, and then either adjust the weight or
        exclude it. Click the Submit button to update the index.
      </p>
      <v-select
        v-model="list"
        :items="indexKeys"
        density="compact"
        variant="solo"
        label="Stock List"
      ></v-select>
      <v-chip-group active-class="primary">
        <v-chip v-for="tag in listMembers" :key="tag" :value="tag" label>
          {{ tag }}
        </v-chip>
      </v-chip-group>
      <v-divider />
      <v-switch
        v-model="excluded"
        :label="excluded ? 'Exclude' : 'Keep'"
        color="blue-darken-4"
        density="compact"
        hide-details
        inline
        inset
      ></v-switch>
      <v-text-field
        v-model="weight"
        :disabled="excluded"
        label="Weighting %"
        variant="solo"
        color="blue-darken-4"
        density="compact"
        :rules="numberValidationRules"
        hide-details
        inline
        inset
      ></v-text-field>
      <!-- <v-text-field v-model="minWeight" :disabled="excluded" :rules="numberValidationRules" color="blue-darken-4" label="Minimum Weighting" density="compact" variant="solo" hide-details inline inset></v-text-field> -->

      <v-divider></v-divider>
      <template v-for="element in excludedLists" :key="element">
        <TailorComponentListItem :list="element" />
      </template>
    </v-card-text>
    <v-card-actions class="justify-center px-6 py-3">
      <v-btn
        :disabled="!hasValidChanges"
        class="text-white flex-grow-1 text-none"
        color="primary"
        variant="flat"
        @click="submit()"
      >
        Submit
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import { mapActions, mapGetters } from "vuex";
export default {
  name: "StockListSetter",
  data: () => ({
    list: "",
    excluded: false,
    dialog: false,
    weight: 100,
    minWeight: 0,
  }),
  props: {},
  computed: {
    ...mapGetters(["portfolioCustomization", "stockLists"]),
    customizations() {
      return this.portfolioCustomization;
    },
    mutations() {
      return (
        this.customizations.stockModifications.length +
        this.customizations.listModifications.length +
        this.customizations.excludedLists.size +
        this.customizations.excludedTickers.size
      );
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
    listMembers() {
      return this.stockLists[this.list];
    },
    indexKeys() {
      return Object.keys(this.stockLists);
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
  },
  methods: {
    ...mapActions(["excludeList", "modifyList"]),
    submit() {
      if (this.excluded) {
        this.excludeList({
          portfolioName: this.portfolioName,
          list: this.list,
        });
      } else {
        this.modifyList({
          portfolioName: this.portfolioName,
          list: this.list,
          scale: this.weight / 100,
          // 'minWeight': this.minWeight
        });
      }
      this.dialog = false;
    },
  },
};
</script>
