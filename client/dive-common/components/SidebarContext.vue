<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import context from 'dive-common/store/context';

export default defineComponent({
  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String,
      default: undefined,
    },
  },
  setup() {
    const options = computed(() => Object.entries(context.componentMap).map(([value, entry]) => ({
      text: entry.description,
      value,
    })));
    return { context, options };
  },
});
</script>

<template>
  <div>
    <v-card
      v-if="context.state.active !== null"
      :width="width"
      tile
      outlined
      class="d-flex flex-column"
      :class="{ sidebar: !mode, modesidebar: mode }"
      style="z-index:1;"
    >
      <div
        v-if="!mode"
        class="d-flex align-center mx-1"
      >
        <v-select
          :items="options"
          :value="context.state.active"
          dense
          solo
          flat
          hide-details
          style="max-width: 240px;"
          @change="context.toggle($event)"
        />
        <v-spacer />
        <v-btn
          icon
          color="white"
          class="shrink"
          @click="context.toggle(null)"
        >
          <v-icon>
            mdi-close
          </v-icon>
        </v-btn>
      </div>
      <div class="sidebar-content">
        <slot
          v-bind="{ name: context.state.active, subCategory: context.state.subCategory }"
        />
      </div>
    </v-card>
  </div>
</template>

<style scoped lang="scss">
.sidebar {
  height: calc(100vh - 112px);
  overflow-y: hidden;
}
.modesidebar {
  overflow-y: hidden;
  height: calc(100vh - 64px);

}
.sidebar-content {
  overflow-y: auto;
}
</style>
