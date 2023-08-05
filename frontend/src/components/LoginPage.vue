<template>
    <v-card class="mx-auto" max-width="344" title="Login to Provider">
        <v-form v-model="form" @submit.prevent="login">
            <v-container>
                <v-select :readonly="loading" :rules="[required]" v-model="selectedProvider" color="primary"
                    :items="providers" @update:modelValue="providerSelected" label="Provider Type"
                    variant="underlined"></v-select>
                <v-text-field :readonly="loading" :rules="[required]" v-model="key" color="primary" :label="loginDisplay"
                    variant="underlined"></v-text-field>
                <v-text-field :readonly="loading" :rules="[required]" v-model="secret" color="primary"
                    :label="secretDisplay" :append-icon="showPass ? 'mdi-eye' : 'mdi-eye-off'"
                    :type="showPass ? 'text' : 'password'" @click:append="showPass = !showPass"
                    variant="underlined"></v-text-field>
                <v-text-field v-if="extraLogin" :readonly="loading" :rules="[required]" v-model="factor" color="primary"
                    label="Extra Factor" :append-icon="showPass ? 'mdi-eye' : 'mdi-eye-off'"
                    :type="showFactor ? 'text' : 'password'" @click:append="showFactor = !showFactor"
                    variant="underlined"></v-text-field>
                <v-checkbox v-model="saveCredentials" color="secondary" label="Save Login Credentials"></v-checkbox>
            </v-container>

            <v-divider></v-divider>
            <v-alert class="mx-auto square-corners" color="warning" v-if="error">{{ error }}</v-alert>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn :disabled="!form" :loading="loading" color="success" type="submit">
                    Authenticate
                    <v-icon icon="mdi-chevron-right" end></v-icon>
                </v-btn>
            </v-card-actions>
        </v-form>
    </v-card>
</template>
<style scoped>
.square-corners {
    border-radius: 0 !important;
}
</style>
<script>
// Views

import instance from '../api/instance'
import axiosHelpers from '../api/helpers';
import exceptions from '../api/exceptions'
import {
    mapActions
} from 'vuex';
export default {
    name: "LoginPage",
    data() {
        return {
            providers: [],
            selectedProvider: null,
            form: false,
            key: '',
            secret: '',
            factor: '',
            loading: false,
            saveCredentials: false,
            showPass: false,
            showFactor: false,
            error: '',
            extraLogin: false

        };
    },
    computed: {
        keys() {
            return this.$store.getters.keys;
        },
        loginDisplay() {
            if (this.selectedProvider == 'alpaca') {
                return 'API Key'
            }
            else if (this.selectedProvider == 'robinhood') {
                return 'Username'
            }
            return 'Login'
        },
        secretDisplay() {
            if (this.selectedProvider == 'alpaca') {
                return 'API Secret'
            }
            else if (this.selectedProvider == 'robinhood') {
                return 'Password'
            }
            return 'Secret'
        }
    },
    methods: {
        ...mapActions(['setLoggedIn', 'storeSavedValue']),
        required(v) {
            return !!v || 'Field is required'
        },
        providerSelected() {
            let key_key = 'key-'.concat(this.selectedProvider)
            let secret_key = 'secret-'.concat(this.selectedProvider)
            let saved_key_key = this.keys.find(obj => obj.key === key_key)
            let saved_secret_key = this.keys.find(obj => obj.key === secret_key)
            if (saved_key_key) {
                this.key = saved_key_key.value
            }
            if (saved_secret_key) {
                this.secret = saved_secret_key.value
            }
        },
        getProviders() {
            let local = this;
            return instance.get('providers').then((response) => {
                local.providers = response.data.available;
            }).catch((err) => {
                console.log(err);
                setTimeout(local.getProviders, 1000)
            });
        },

        login() {
            let local = this;
            this.loading = true;
            this.error = '';
            this.extraLogin = false;
            let command = {
                'key': this.key,
                'secret': this.secret,
                'provider': this.selectedProvider,
            }
            if (this.factor) {
                command = {
                    'key': this.key,
                    'secret': this.secret,
                    'provider': this.selectedProvider,
                    'extra_factor': this.factor
                }
            }
            return instance.post('login', command).then(() => {
                if (this.saveCredentials) {
                    this.storeSavedValue({
                        'key': 'key-'.concat(this.selectedProvider),
                        'value': this.key
                    });
                    this.storeSavedValue({
                        'key': 'secret-'.concat(this.selectedProvider),
                        'value': this.secret
                    });
                }
                local.$router.push({
                    path: 'portfolio_list'
                })

            }).catch((exc) => {
                if (exc instanceof exceptions.auth_extra) {
                    this.extraLogin = true;
                    this.error = axiosHelpers.getErrorMessage('Extra authentication info required, provide and re-login');
                } else {
                    this.error = axiosHelpers.getErrorMessage(exc);
                }

            }).finally(() => {
                this.factor = '';
                this.loading = false;

            });
        },
    },
    mounted() {
        this.getProviders()
    },
};
</script>
