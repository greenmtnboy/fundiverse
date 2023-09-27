<template>
    <v-dialog v-model="dialog" max-width="500" min-width=400>
        <template v-slot:activator="{ props }">
            <v-btn data-testid="add-portfolio" class="text-none" color="primary" variant="outlined" v-bind="props">
                Add Portfolio
            </v-btn>
        </template>
        <v-card class="mx-auto" min-width="344" title="New Portfolio">
            <v-form v-model="form">
                <v-container>
                    <v-text-field id="input-add-portfolio-name" test-id="input-add-portfolio-name" :readonly="loading"
                        :rules="[required]" v-model="name" color="primary" title="New Portfolio Name" type="portfolio-name"
                        label="New Portfolio Name" variant="underlined">
                    </v-text-field>
                    <v-text-field :readonly="loading" :rules="[required]" v-model="target_size" color="primary"
                        label="Target Size" variant="underlined">
                    </v-text-field>
                </v-container>
                <v-divider></v-divider>
                <v-alert class="mx-auto square-corners" color="warning" v-if="error">{{ error }}</v-alert>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn data-testid="btn-add-portfolio-submit" :disabled="!form" :loading="loading" color="success"
                        @click="localAddNewCompositePortfolio">
                        Create
                        <v-icon icon="mdi-chevron-right" end></v-icon>
                    </v-btn>
                </v-card-actions>
            </v-form>
        </v-card>
    </v-dialog>
</template>
<style scoped>
.square-corners {
    border-radius: 0 !important;
}
</style>
<script lang="ts">
import {
    mapActions
} from 'vuex';
export default {
    name: "AddPortfolioPopup",
    data() {
        return {
            name: '',
            form: false,
            loading: false,
            error: '',
            dialog: false,
            target_size: 1000
        };
    },
    props: {
    },
    computed: {

    },
    methods: {
        ...mapActions(['addNewCompositePortfolio']),
        localAddNewCompositePortfolio() {
            this.addNewCompositePortfolio({
                name: this.name,
                target_size: this.target_size
            }).then(() => {
                this.dialog = false;
                this.name = '';
            }).catch((e) => {
                this.error = e.message;
            });
        },
        required(v) {
            return !!v || 'Field is required'
        },
    },
};
</script>
