<template>
  <span class="px-2">
    <v-tooltip bottom>
      <template v-slot:activator="{ props }">
        <v-btn icon v-bind="props" density="compact">{{ labelText }}</v-btn>
      </template>
      <span>{{ text }}</span>
    </v-tooltip>
  </span>
</template>
<script lang="ts">
export default {
  name: "IconTooltip",
  props: {
    text: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: false,
    },
  },
  computed: {
    labelText() {
      return this.label || "?";
    },
  },
};
</script>
