<template>
    <v-dialog v-model="dialog" max-width="500" min-width=400>
        <template v-slot:activator="{ props }">
            <v-tooltip v-if="loginSuccess">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" transition="fade-transition" class="text-none" color="green" size="compact" icon>
                        <v-icon>mdi-check</v-icon>
                    </v-btn>
                </template>
                <span>You are authenticated to this provider</span>
            </v-tooltip>
            <v-tooltip v-else-if="error">
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" @click="forceOpenModal" color="primary">
                        {{ label }}
                    </v-btn>
                </template>
                <span>Unable to automatically authenticate</span>
            </v-tooltip>
            <v-btn v-else :loading="loading" @click="loadDefaults" v-bind="props">
                {{ label }}
            </v-btn>
        </template>
        <v-card class="mx-auto" min-width="344" :title="selectedProvider ? `Login to ${ selectedProvider}` : 'Provider' "
        >
            <v-form v-model="form" @submit.prevent="login">
                <v-container>

                    <v-select :readonly="loading || !providerSelectable" :rules="[required]" v-model="selectedProvider"
                        color="primary" :items="availableProviders" @update:modelValue="providerSelected"
                        label="Provider Type" variant="underlined"></v-select>
                    <template v-if="providerKeyValues[this.selectedProvider]" v-for="key in providerLoginKeys">
                        <v-text-field v-if="key.type == 'secret'" :readonly="loading" :rules="[required]"
                            v-model="providerKeyValues[selectedProvider][key.key]"
                            color="primary" :label="key.label"
                            variant="underlined" :append-icon="showPass ? 'mdi-eye' : 'mdi-eye-off'"
                            :type="showPass ? 'text' : 'password'" @click:append="showPass = !showPass"></v-text-field>
                        <v-text-field v-else :readonly="loading" :rules="[required]"
                            v-model="providerKeyValues[selectedProvider][key.key]"
                            color="primary" :label="key.label"
                            variant="underlined"></v-text-field>
                    </template>
                    <v-text-field v-if="extraLogin" :readonly="loading" :rules="[required]" v-model="factor" color="primary"
                        label="Extra Factor" :append-icon="showFactor ? 'mdi-eye' : 'mdi-eye-off'"
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
<script lang="ts">
// Views

import instance from '/src/api/instance'
import axiosHelpers from '/src/api/helpers';
import exceptions from '/src/api/exceptions'
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
            error: '' as string,
            extraLogin: false,
            dialog: false,
            providerKeyValues: {} as any
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
            return this.provider == null ? 'Add Provider' : 'Login'
        },
        availableProviders() {
            return this.providers.filter(item => !this.providerKeys.includes(item));
        },
        providerLoginKeys() {
            return this.getProviderLoginKeys(this.selectedProvider)
        },
    },
    methods: {

        ...mapActions(['setLoggedIn', 'probeLogin', 'storeSavedValue', 'refreshCompositePortfolio', 'pushEmptyProvider']),
        required(v) {
            return !!v || 'Field is required'
        },
        forceOpenModal() {
            // this.getDefaults()
            this.dialog = true;
        },
        getProviderLoginKeys(provider) {
                if (['alpaca', 'alpaca_paper'].includes(provider)) {
                    return [{ 'key': 'key', 'label': 'API Key' },
                    { 'key': 'secret', 'label': 'API Secret', 'type': 'secret' }]
                }
                else if (provider == 'robinhood') {
                    return [{ 'key': 'key', 'label': 'Username' },
                    { 'key': 'secret', 'label': 'Password', 'type': 'secret' }]
                }
                else if (['webull', 'webull_paper'].includes(provider)) {
                    return [{ 'key': 'key', 'label': 'Email' },
                    { 'key': 'secret', 'label': 'Password', 'type': 'secret' },
                    { 'key': 'device_id', 'label': 'Device ID', 'type': 'secret' },
                    { 'key': 'trading_pin', 'label': 'Trading Pin', 'type': 'secret' }]
                }
                return [{ 'key': 'key', 'label': 'Login' },
                { 'key': 'secret', 'label': 'Password', 'type': 'secret' }]
        },
        getDefaults(provider) {
            // loop through providerKeys
            let keys = this.getProviderLoginKeys(provider)
            let values = {}
            this.providerKeyValues[provider] = {}
            let foundAll = true
            for (let i = 0; i < keys.length; i++) {
                let key = keys[i].key.concat('-').concat(provider)
                let saved_key_value = this.keys.find(obj => obj.key === key)
                if (saved_key_value) {
                    values[keys[i].key] = saved_key_value.value
                }
                else {
                    values[keys[i].key] = null
                    foundAll = false
                }
            }
            this.providerKeyValues[provider] = values
            return foundAll
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
                ...this.providerKeyValues[this.selectedProvider],
                'provider': this.selectedProvider,
            }
            if (this.factor) {
                command = { ...command, 'extra_factor': this.factor }
            }
            return instance.post('login', command).then(() => {
                this.setLoggedIn({ 'provider': this.selectedProvider });

                if (this.saveCredentials) {
                    for (let i = 0; i < this.providerLoginKeys.length; i++) {
                        let key = this.providerLoginKeys[i].key.concat('-').concat(this.selectedProvider)
                        this.storeSavedValue({
                            'key': key,
                            'value': this.providerKeyValues[this.selectedProvider][this.providerLoginKeys[i].key]
                        });
                    }
                }
                this.dialog = false;
                if (this.provider == null) {
                    this.pushEmptyProvider({ portfolioName: this.portfolioName, key: this.selectedProvider })
                    this.probeLogin({ provider: this.selectedProvider })
                    if (refresh) {
                        return this.refreshCompositePortfolio({ portfolioName: this.portfolioName })
                    }

                }
                else {
                    this.probeLogin({ provider: this.provider })
                    if (refresh) {
                        return this.refreshCompositePortfolio({ portfolioName: this.portfolioName })
                    }

                }

            }).catch((exc) => {
                if (exc instanceof exceptions.auth_extra) {
                    this.extraLogin = true;
                    this.error = 'Extra authentication info required, provide and re-submit login'
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

                Promise.all([this.probeLogin({ provider: this.provider }), this.getDefaults(this.provider)]).then(() => {
                    if (!this.loginSuccess) {
                        this.login(false)
                    }
                })

            }
        })

    },
};
</script>
