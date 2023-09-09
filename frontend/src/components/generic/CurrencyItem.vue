<template>

    <span v-if="loading" class="box-placeholder">
        {{ value.currency }}<span class="text">xxxxxxx</span>
    </span>
    <span v-else>
        {{ value.currency }}{{ Math.round(value.value * 100) / 100 }}
    </span>
</template>
<style>


.box-placeholder .text {

    background-color: #444;
    color:#444;
    height: 12px;
    border-radius: 100px;
    margin: 5px 0;
    min-width: 100px;
    opacity: 0.1;
    animation: fading 1.5s infinite;
}

.box-placeholder .text:first-child {
    margin-top: 0;
}

.box-placeholder .text:last-child {
    margin-bottom: 0;
}

.box-placeholder .text.link {
    background-color: var(--blue);
    opacity: 0.4;
}

.box-placeholder .text.line {
    width: 100%;
}

.box-placeholder .text.category {
    width: 100px;
    margin-bottom: 10px;
}

.box-placeholder h4.text {
    height: 20px;
    margin: 3px 0;
    opacity: 0.2;
}

.box-placeholder .image {
    background-color: #f9f9f9;
}

@keyframes fading {
    0% {
        opacity: 0.1;
    }

    50% {
        opacity: 0.2;
    }

    100% {
        opacity: 0.1;
    }
}
</style>
<script lang="ts">

export default {
    name: "CurrencyItem",
    props: {
        value: {
            type: Object,
            required: true
        },
        loading: {
            type: Boolean,
            required: false,
            default: false
        }
    },

};
</script>