<template>
    <v-btn color="red" prependIcon="mdi-cancel" @click="dialog = true">Delete</v-btn>
    <v-dialog v-model="dialog" max-width="400">
        <v-card>
            <v-card-title>Confirm</v-card-title>
            <v-card-text>
                Are you sure you want to perform this action?
            </v-card-text>
            <v-card-actions>
                <v-btn color="error" @click="confirm">Confirm</v-btn>
                <v-btn @click="cancel">Cancel</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
  
<script lang="ts">
export default {
    data() {
        return {
            dialog: false,
        };
    },
    props: {
        text: {
            type: String,
            required: true,
        },
        onClick: {
            type: Function,
            required: true,
        },
    },
    methods: {
        confirm() {
            this.onClick();
            this.dialog = false; // Close the dialog
        },
        cancel() {
            this.dialog = false; // Close the dialog
        },
    },
};
</script>