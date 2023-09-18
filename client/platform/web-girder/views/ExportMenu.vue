<script lang="ts">
import {
  computed,
  defineComponent, ref,
} from '@vue/composition-api';
import {
  getUri,
} from 'platform/web-girder/api';

import { useStore, RootlessLocationType } from '../store/types';
import FilterImport from './FilterImport.vue';

export default defineComponent({
  name: 'ExportMenu',
  components: {
    FilterImport,
  },
  props: {
    buttonOptions: {
      type: Object,
      default: () => ({}),
    },
    menuOptions: {
      type: Object,
      default: () => ({}),
    },
  },
  setup() {
    const store = useStore();
    const locationStore = store.state.Location;
    const menuOpen = ref(false);
    const id = computed(() => locationStore.location
    && (locationStore.location as RootlessLocationType)._id);
    const exportLinks = () => {
      const idbase = locationStore.location && (locationStore.location as RootlessLocationType)._id;
      const url = `UMD_dataset/links/${idbase}`;
      const link = getUri({ url });
      window.location.assign(link);
    };

    const exportAnnotations = (filtered = false) => {
      const idbase = locationStore.location && (locationStore.location as RootlessLocationType)._id;
      let url = `UMD_dataset/recursive_export/${idbase}`;
      if (filtered) {
        url = `${url}?applyFilter=true`;
      }
      const link = getUri({ url });
      window.location.assign(link);
    };
    return {
      locationStore,
      exportLinks,
      exportAnnotations,
      menuOpen,
      id,
    };
  },
});
</script>

<template>
  <v-menu
    v-model="menuOpen"
    :close-on-content-click="false"
    :nudge-width="120"
    v-bind="menuOptions"
    max-width="280"
  >
    <template #activator="{ on: menuOn }">
      <v-tooltip bottom>
        <template #activator="{ on: tooltipOn }">
          <v-btn
            v-bind="buttonOptions"
            v-on="{ ...tooltipOn, ...menuOn }"
          >
            <v-icon color="accent">
              mdi-table
            </v-icon>
            <span
              v-show="!$vuetify.breakpoint.mdAndDown || buttonOptions.block"
              class="pl-1"
            >
              Export
            </span>
            <v-spacer />
            <v-icon v-if="menuOptions.right">
              mdi-chevron-right
            </v-icon>
          </v-btn>
        </template>
        <span>Download media and annotations</span>
      </v-tooltip>
    </template>
    <template>
      <v-card
        outlined
      >
        <v-card-title>
          Export options
        </v-card-title>
        <v-card-actions>
          <v-btn
            v-if="locationStore &&
              locationStore.location && locationStore.location._modelType === 'folder'"
            class="ma-0"
            text
            small
            @click="exportLinks()"
          >
            <v-icon
              left
              color="accent"
            >
              mdi-file-delimited
            </v-icon>
            Export Links
          </v-btn>
        </v-card-actions>
        <v-card-actions>
          <v-btn
            v-if="locationStore &&
              locationStore.location && locationStore.location._modelType === 'folder'"
            class="ma-0"
            text
            small
            @click="exportAnnotations()"
          >
            <v-icon
              left
              color="accent"
            >
              mdi-file-delimited
            </v-icon>
            Export Annotations
          </v-btn>
        </v-card-actions>
        <v-card-actions>
          <v-btn
            v-if="locationStore &&
              locationStore.location && locationStore.location._modelType === 'folder'"
            class="ma-0"
            text
            small
            @click="exportAnnotations(true)"
          >
            <v-icon
              left
              color="accent"
            >
              mdi-file-delimited
            </v-icon>
            Export Annotations Filtered
            <v-icon
              right
              color="accent"
            >
              mdi-filter
            </v-icon>
          </v-btn>
        </v-card-actions>
        <v-card-actions>
          <filter-import :id="id" />
        </v-card-actions>
      </v-card>
    </template>
  </v-menu>
</template>
