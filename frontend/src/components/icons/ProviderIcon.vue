<template>
    <v-avatar>
        <AlpacaIcon v-if="iconType === 'alpaca'"></AlpacaIcon>
        <template v-else-if="iconType === 'robinhood'">
            <v-img :src="robinhoodSrc" alt="'Robinhood Logo'" />
        </template>
    </v-avatar>
</template>
<script>
import AlpacaIcon from './AlpacaIcon.vue'
export default {
    name: 'ProviderIcon',
    data() {
        return {
            robinhoodSrc: require('@/assets/robinhood.png'), // Replace with the correct path to your .png file
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