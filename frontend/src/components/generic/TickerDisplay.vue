<template>
    <v-tooltip v-on:update:modelValue="load()" :text="text">
        <template v-slot:activator="{ props }">
            <span v-bind="props">
                {{ ticker }}
            </span>
        </template>
    </v-tooltip>
</template>
<style></style>
<script lang="ts">
import instance from '/src/api/instance'

export default {
    name: "Ticker Display",
    data() {
        return {
            text: 'Tooltip',
            loaded: false,
            loading: false
        };
    },
    props: {
        ticker: {
            type: String,
            required: true,
        },
    },
    methods: {
        load() {
            if (this.loading || this.loaded) {
                return;
            }
            this.loading = true;
            this.text = 'Loading...'
            instance.get(`stock_info/${this.ticker}`).then((resp) => {
                this.text = `${resp.data.name} (${resp.data.exchange})`
                this.loading = false
                this.loaded = true
            }).catch((e)=>{
                this.text = `Error loading ticker details: ${e}`
                this.loading = false
                this.loaded = true
            })
        },
    }

};
</script>