<template>
  <v-avatar>
    <AlpacaIcon v-if="iconType === 'alpaca'" color="goldenrod"></AlpacaIcon>
    <AlpacaIcon
      v-else-if="iconType === 'alpaca_paper'"
      color="gray"
    ></AlpacaIcon>
    <template v-else-if="iconType === 'webull'">
      <v-img class="webull-color-change" :src="webullSrc" alt="'Webull Logo'" />
    </template>
    <template v-else-if="iconType === 'webull_paper'">
      <v-img :src="webullSrc" alt="'Webull Logo'" />
    </template>
    <template v-else-if="iconType === 'robinhood'">
      <v-img :src="robinhoodSrc" alt="'Robinhood Logo'" />
    </template>
    <template v-else-if="iconType === 'schwab'">
      <v-img :src="schwabSrc" alt="'Charles Schwab Logo'" />
    </template>
  </v-avatar>
</template>
<style>
.webull-color-change {
  /* Apply a CSS filter to change the color */
  filter: hue-rotate(330deg) saturate(500%);
}
</style>
<script lang="ts">
import AlpacaIcon from "./AlpacaIcon.vue";
import robinhoodURL from "/src/assets/robinhood.png";
import webullPNG from "/src/assets/webull.png";
import schwabSVG from "/src/assets/schwab.svg";
export default {
  name: "ProviderIcon",
  data() {
    return {
      robinhoodSrc: robinhoodURL,
      webullSrc: webullPNG,
      schwabSrc: schwabSVG,
    };
  },
  components: {
    AlpacaIcon,
  },
  props: {
    iconType: {
      type: String,
      required: true,
    },
  },
};
</script>
