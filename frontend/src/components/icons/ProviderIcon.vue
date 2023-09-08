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
export default {
    name: 'ProviderIcon',
    data() {
        return {
            robinhoodSrc: require('/src/assets/robinhood.png'), // Replace with the correct path to your .png file
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