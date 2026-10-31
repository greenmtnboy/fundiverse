<template>
  <v-btn
    :loading="exporting"
    :disabled="disabled"
    :data-testid="`btn-export-${portfolioName}`"
    class="d-flex flex-column"
    @click="exportDatabase()"
    >Export Bundle
  </v-btn>
  <v-snackbar v-model="showExportError" color="error" timeout="6000">
    {{ exportError }}
  </v-snackbar>
  <v-snackbar v-model="showSavedTo" :color="hasWarnings ? 'warning' : 'success'"
    :timeout="hasWarnings ? 10000 : 6000">
    <div v-if="savedTo">Saved to {{ savedTo }}</div>
    <div v-if="skipped.length" data-testid="export-skipped-providers">
      Not included (log in to export): {{ skipped.join(", ") }}
    </div>
    <div v-if="expired.length" data-testid="export-expired-providers">
      Login expired, so saved holdings were used and dividends not updated: {{ expired.join(", ") }}.
      Log in again to refresh them.
    </div>
    <div v-if="compositionError" data-testid="export-composition-error">
      Target composition not included: {{ compositionError }}
    </div>
  </v-snackbar>
</template>

<script lang="ts">
import { ipcRenderer } from "electron";
import instance from "/src/api/instance";
import { requestDatabaseExport } from "/src/helpers/exportDatabase";

export default {
  name: "ExportDatabaseButton",
  props: {
    portfolioName: {
      type: String,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      exporting: false,
      exportError: "",
      showExportError: false,
      savedTo: "",
      showSavedTo: false,
      skipped: [] as Array<string>,
      expired: [] as Array<string>,
      compositionError: "" as string | null,
    };
  },
  computed: {
    hasWarnings(): boolean {
      return (
        this.skipped.length > 0 ||
        this.expired.length > 0 ||
        Boolean(this.compositionError)
      );
    },
  },
  methods: {
    async exportDatabase() {
      // build the DuckDB file and target composition on the backend, then
      // hand both to the user as one zip
      this.exporting = true;
      this.savedTo = "";
      try {
        const result = await requestDatabaseExport(this.portfolioName);
        this.skipped = result.providers_skipped;
        // a provider that was skipped outright is already listed above
        this.expired = Object.keys(result.provider_errors || {}).filter(
          (provider) => !this.skipped.includes(provider),
        );
        this.compositionError = result.composition_error;
        const response = await instance.get(
          `database/download_bundle/${this.portfolioName}`,
          { responseType: "blob" },
        );
        const fileName = `${this.portfolioName}.zip`;
        if (ipcRenderer) {
          // electron: let the user choose where it goes
          const savedTo = await ipcRenderer.invoke(
            "save-file",
            fileName,
            await response.data.arrayBuffer(),
          );
          if (savedTo) {
            this.savedTo = savedTo;
            this.showSavedTo = true;
          }
        } else {
          const url = URL.createObjectURL(response.data);
          const link = document.createElement("a");
          link.href = url;
          link.download = fileName;
          link.click();
          // give the browser a tick to start the download before freeing the blob
          setTimeout(() => URL.revokeObjectURL(url), 1000);
          // the browser shows its own download; only speak up if something was left out
          this.showSavedTo = this.hasWarnings;
        }
      } catch (error: any) {
        console.error("Database export failed:", error);
        this.exportError =
          error.response?.data?.detail ||
          error.message ||
          "Failed to export portfolio database";
        this.showExportError = true;
      } finally {
        this.exporting = false;
      }
    },
  },
};
</script>
