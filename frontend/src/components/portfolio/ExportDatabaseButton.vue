<template>
  <v-btn
    :loading="exporting"
    :disabled="disabled"
    :data-testid="`btn-export-${portfolioName}`"
    class="d-flex flex-column"
    @click="exportDatabase()"
    >Export Database
  </v-btn>
  <v-snackbar v-model="showExportError" color="error" timeout="6000">
    {{ exportError }}
  </v-snackbar>
  <v-snackbar v-model="showSavedTo" :color="skipped.length ? 'warning' : 'success'"
    :timeout="skipped.length ? 10000 : 6000">
    <div v-if="savedTo">Saved to {{ savedTo }}</div>
    <div v-if="skipped.length" data-testid="export-skipped-providers">
      Not included (log in to export): {{ skipped.join(", ") }}
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
    };
  },
  methods: {
    async exportDatabase() {
      // build the DuckDB file on the backend, then hand it to the user as a download
      this.exporting = true;
      this.savedTo = "";
      try {
        const result = await requestDatabaseExport(this.portfolioName);
        this.skipped = result.providers_skipped;
        const response = await instance.get(
          `database/download/${this.portfolioName}`,
          { responseType: "blob" },
        );
        const fileName = `${this.portfolioName}.db`;
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
          this.showSavedTo = this.skipped.length > 0;
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
