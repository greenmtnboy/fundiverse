<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ props }">
      <v-btn
        class="text-none"
        color="primary"
        variant="outlined"
        data-testid="btn-upload-exclusions"
        v-bind="props"
      >
        Upload Exclusions
      </v-btn>
    </template>

    <v-card title="Upload Exclusions">
      <v-card-text>
        <p class="pb-4">
          Choose a text or CSV file with one ticker per line. Only the first
          column is read, a ticker or symbol header is fine, and lines starting
          with # are skipped.
        </p>
        <v-file-input
          v-model="file"
          label="Exclusion file"
          accept=".csv,.txt"
          variant="underlined"
          density="compact"
          show-size
          data-testid="input-exclusion-file"
          @update:modelValue="readFile"
        ></v-file-input>
        <v-alert
          v-if="error"
          color="warning"
          density="compact"
          data-testid="exclusion-upload-error"
          >{{ error }}</v-alert
        >
        <v-alert
          v-else-if="parsed"
          color="info"
          density="compact"
          data-testid="exclusion-upload-summary"
        >
          {{ newTickers.length }} new exclusions,
          {{ parsed.tickers.length - newTickers.length }} already excluded.
          <span v-if="parsed.invalid.length">
            {{ parsed.invalid.length }} lines skipped, starting with
            "{{ parsed.invalid[0] }}".
          </span>
        </v-alert>
      </v-card-text>
      <v-divider></v-divider>

      <v-card-actions class="justify-center px-6 py-3">
        <v-btn
          class="flex-grow-1 text-none"
          variant="plain"
          @click="close()"
        >
          Exit
        </v-btn>
        <v-btn
          :disabled="!newTickers.length"
          class="text-white flex-grow-1 text-none"
          color="primary"
          variant="flat"
          data-testid="btn-exclusion-upload-submit"
          @click="submit()"
        >
          Exclude {{ newTickers.length || "" }} Stocks
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { mapActions, mapGetters } from "vuex";

import {
  ParsedExclusions,
  parseExclusionFile,
} from "/src/helpers/exclusionFile";

export default {
  name: "TailorExclusionUpload",
  data() {
    return {
      dialog: false,
      file: null as File | File[] | null,
      parsed: null as ParsedExclusions | null,
      error: "",
    };
  },
  props: {
    portfolioName: {
      type: String,
      required: true,
    },
  },
  computed: {
    ...mapGetters(["portfolioCustomizations"]),
    newTickers(): string[] {
      if (!this.parsed) {
        return [];
      }
      const existing =
        this.portfolioCustomizations.get(this.portfolioName)?.excludedTickers ??
        new Set();
      return this.parsed.tickers.filter((ticker) => !existing.has(ticker));
    },
  },
  methods: {
    ...mapActions(["excludeStocks"]),
    async readFile(selected: File | File[] | null) {
      this.parsed = null;
      this.error = "";
      const file = Array.isArray(selected) ? selected[0] : selected;
      if (!file) {
        return;
      }
      try {
        const parsed = parseExclusionFile(await file.text());
        if (parsed.tickers.length) {
          this.parsed = parsed;
        } else {
          this.error = `No tickers found in ${file.name}.`;
        }
      } catch (e) {
        this.error = `Could not read ${file.name}.`;
      }
    },
    close() {
      this.dialog = false;
      this.file = null;
      this.parsed = null;
      this.error = "";
    },
    submit() {
      this.excludeStocks({
        portfolioName: this.portfolioName,
        tickers: this.newTickers,
      });
      this.close();
    },
  },
};
</script>
