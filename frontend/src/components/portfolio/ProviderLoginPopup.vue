<template>
    <v-dialog v-model="dialog" max-width="500" min-width=400>
        <template v-slot:activator="{ props }">
            <v-tooltip v-if="loginSuccess">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" transition="fade-transition" class="text-none"
                     color="green" size="compact" icon>
                        <v-icon>mdi-check</v-icon>
                    </v-btn>
                </template>
                <span>You are authenticated to this provider</span>
            </v-tooltip>
            <v-tooltip v-else-if="error">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props"  @click="forceOpenModal"   color="primary" >
                        {{ label }}
                    </v-btn>
                </template>
                <span>Unable to automatically authenticate</span>
            </v-tooltip>
            <v-btn v-else :loading="loading" @click="loadDefaults" v-bind="props">
                {{ label }}
            </v-btn>
        </template>
        <v-card class="mx-auto" min-width="344" title="Login to Provider">
            <v-form v-model="form" @submit.prevent="login">
                <v-container>
                    <v-select :readonly="loading || !providerSelectable" :rules="[required]" v-model="selectedProvider"
                        color="primary" :items="availableProviders" @update:modelValue="providerSelected"
                        label="Provider Type" variant="underlined"></v-select>
                    <v-text-field :readonly="loading" :rules="[required]" v-model="key" color="primary"
                        :label="loginDisplay" variant="underlined"></v-text-field>
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
    </v-dialog>
</template>
<style scoped>
.square-corners {
    border-radius: 0 !important;
}
</style>
<script>
// Views

import instance from '@/api/instance'
import axiosHelpers from '@/api/helpers';
import exceptions from '@/api/exceptions'
import {
    mapActions, mapGetters
} from 'vuex';
export default {
    name: "LoginPage",
    data() {
        let providerSelectable = this.provider == null;
        return {
            providers: [],
            providerSelectable: providerSelectable,
            selectedProvider: this.provider,
            form: false,
            key: '',
            secret: '',
            factor: '',
            loading: false,
            saveCredentials: false,
            showPass: false,
            showFactor: false,
            error: '',
            extraLogin: false,
            dialog: false,
        };
    },
    props: {
        provider: {
            type: String,
            required: false,
            default: null
        },
        portfolioName: {
            type: String,
            required: true,
        },
        providerKeys: {
            type: Array,
            required: false,
            default: function () {
                return [];
            }
        }
    },
    computed: {
        ...mapGetters(['activeProviders', 'keys']),
        loginSuccess() {
            return this.activeProviders.includes(this.provider)
        },
        label() {
            if (this.error) {
                return 'Fix Login'
            }
            return this.provider == null ? 'Connect Provider' : 'Login'
        },
        availableProviders() {
            return this.providers.filter(item => !this.providerKeys.includes(item));
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

        ...mapActions(['setLoggedIn', 'probeLogin', 'storeSavedValue', 'refreshCompositePortfolio', 'pushEmptyProvider']),
        required(v) {
            return !!v || 'Field is required'
        },
        forceOpenModal(){
            // this.getDefaults()
            this.dialog = true;
        },
        getDefaults(provider) {
            let key_key = 'key-'.concat(provider)
            let secret_key = 'secret-'.concat(provider)
            let saved_key_key = this.keys.find(obj => obj.key === key_key)
            let saved_secret_key = this.keys.find(obj => obj.key === secret_key)
            if (saved_key_key) {
                this.key = saved_key_key.value
            }
            if (saved_secret_key) {
                this.secret = saved_secret_key.value
            }

            return saved_key_key && saved_secret_key
        },
        providerSelected() {
            this.getDefaults(this.selectedProvider)
        },
        getProviders() {
            let local = this;
            return instance.get('providers').then((response) => {
                local.providers = response.data.available;
            }).catch(() => {
                setTimeout(local.getProviders, 1000)
            });
        },
        async loadDefaults() {
            this.getDefaults(this.provider)
        },
        async autoLogin() {
            const defaults = this.getDefaults(this.provider)
            if (defaults) {
                this.loading = true;
                await this.login()
            }
        },

        async login(refresh = true) {
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
                this.setLoggedIn({ 'provider': this.selectedProvider });

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
                this.dialog = false;
                if (this.provider == null) {
                    this.pushEmptyProvider({ portfolioName: this.portfolioName, key: this.selectedProvider })
                    this.probeLogin({provider: this.selectedProvider})
                    if (refresh) {
                        return this.refreshCompositePortfolio({ portfolioName: this.portfolioName})
                    }

                }
                else {
                    this.probeLogin({provider: this.provider})
                    if (refresh) {
                        return this.refreshCompositePortfolio({ portfolioName: this.portfolioName })
                    }

                }

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
    async mounted() {
        this.getProviders().then(() => {
            if (this.provider) {
                if (this.loginSuccess) {
                    return
                }

                Promise.all([this.probeLogin({provider:this.provider}), this.getDefaults(this.provider)]).then(() => {
                    if (this.key && this.secret && !this.loginSuccess) {
                        this.login(false)
                    }
                })

            }
        })

    },
};
</script>
