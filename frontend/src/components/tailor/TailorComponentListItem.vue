<template>
    <v-list-item>
        <v-row>
            <v-col cols="3" class="d-flex align-center">
                <v-list-item-title> <v-btn density="compact" @click="openGithub" icon>
                        <v-icon>mdi-github</v-icon>
                    </v-btn><span class="px-1">{{ list }}</span>
                    <v-chip :color="weight >= 1 ? 'green' : 'red'" v-if="weight" small outlined>{{ weight * 100 }}%</v-chip>
                </v-list-item-title>
            </v-col>
            <v-col cols="9">
                <v-chip-group class="d-flex align-center" active-class="primary">
                    <v-chip v-for="tag in displayedTags" :key="tag" :value="tag" label>
                        {{ tag }}
                    </v-chip>
                    <v-chip v-if="tags.length > displayedTags.length" label>
                        ...
                    </v-chip>
                    <v-tooltip v-if="tags.length > displayedTags.length">

                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" @click="toggleShowAll" icon density="compact">
                                <v-icon>mdi-eye</v-icon>
                            </v-btn>

                        </template>
                        <span>Show All Tags</span>
                    </v-tooltip>
                    <v-tooltip v-else-if="tags.length > maxDisplayedTags">
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props" @click="toggleShowAll" icon density="compact">
                                <v-icon>mdi-eye-off-outline</v-icon>
                            </v-btn>
                        </template>
                        <span>Collapse Tags</span>
                    </v-tooltip>
                </v-chip-group>
            </v-col>

        </v-row>

        <template v-slot:append>

            <v-tooltip>
                <template v-slot:activator="{ props }">
                    <v-btn v-bind="props" @click="action => removeListExclusion(list)" icon density="compact">
                        <v-icon color="warning">mdi-cancel</v-icon>
                    </v-btn>
                </template>
                <span>Remove Exclusion</span>
            </v-tooltip>
        </template>
    </v-list-item>
</template>

<script>
import {
    mapActions,
    mapGetters
} from 'vuex';

const {
    shell
} = require('electron');

export default {
    name: "TailorComponentListItem",
    data() {
        return {
            showAllTags: false,
            maxDisplayedTags: 10,
            githubLink: ""
        };
    },
    created() {
        this.githubLink = `https://github.com/greenmtnboy/py-portfolio-index/blob/main/py_portfolio_index/bin/lists/${this.list}.csv`;
    },
    props: {
        list: {
            type: String,
            required: true
        },
        weight: {
            type: Number,
            required: false
        }
    },
    computed: {
        ...mapGetters(['stockLists']),
        tags() {
            const list = this.stockLists[this.list];
            if (!list) {
                return [];
            }
            return list
        },
        displayedTags() {
            if (this.showAllTags) {
                return this.tags;
            } else {
                if (!this.tags) {
                    return [];
                }
                return this.tags.slice(0, this.maxDisplayedTags);
            }
        },
    },
    methods: {
        ...mapActions(['removeListExclusion']),
        toggleShowAll() {
            this.showAllTags = !this.showAllTags;
        },
        openGithub() {
            shell.openExternal(this.githubLink);
        }
    },
};
</script>
