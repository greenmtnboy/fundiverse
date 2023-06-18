<template>
  <v-list-item  >
    <div >{{ element.ticker }}<p class="text-medium-emphasis">{{ elementWeight }}%</p></div>
    <!-- <v-row> {{ elementWeight }}%</v-row> -->
    <template v-slot:append>
      <v-btn  :loading="loading" @click="onClickWrapper"
       icon density="compact">
        <v-icon  :loading="loading" color="warning">mdi-cancel</v-icon>
      </v-btn>

    </template>
  </v-list-item>
</template>
<script>
import TargetPortfolioElementModel from '../models/TargetPortfolioElementModel';

export default {
  name: "TargetPortfolioElement",
  data() {
    return {
      loading: false
    }
  },
  methods: {
    onClickWrapper() {
      this.loading = true;
      if (this.onClick) {
        this.onClick(this.element).then(() => { }).finally(() => { this.loading = false });
      } else {
        this.loading = false;
      }
    }
  },
  props: {
    element: {
      type: TargetPortfolioElementModel,
      required: true,
    },
    onClick: {
      type: Function,
      required: false,
    }
  },
  computed: {
    elementWeight() {
      return Math.round(this.element.weight * 10000) / 100;
    },
  }
};
</script>