<template>
    <v-avatar>
        <AlpacaIcon v-if="iconType === 'alpaca'" color="goldenrod"></AlpacaIcon>
        <AlpacaIcon v-else-if="iconType === 'alpaca_paper'" color="gray"></AlpacaIcon>
        <template v-else-if="iconType === 'robinhood'">
            <v-img :src="robinhoodSrc" alt="'Robinhood Logo'" />
        </template>
    </v-avatar>
</template>
<script lang="ts">
import AlpacaIcon from './AlpacaIcon.vue'
import robinhoodURL from '/src/assets/robinhood.png'
export default {
    name: 'ProviderIcon',
    data() {
        return {
            robinhoodSrc: robinhoodURL, // Replace with the correct path to your .png file
        };
    },
    components: {
        AlpacaIcon
    },
    props: {
        iconType: {
            type: String,
            required: true
        }
    }
}
</script>