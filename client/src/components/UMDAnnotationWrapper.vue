<script lang="ts">
import {
  defineComponent, PropType,
} from '@vue/composition-api';
import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import UMDAnnotation from './UMDAnnotation.vue';
import UMDChangepoint from './UMDChangepoint.vue';
import UMDRemediation from './UMDRemediation.vue';
export default defineComponent({
  name: 'UMDAnnotationWrapper',
  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDAnnotation,
    UMDChangepoint,
    UMDRemediation,
  },
  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String as PropType<'VAE' | 'norms' | 'changepoint' | 'emotion' | 'remediation' | 'review'>,
      default: 'review',
    },
  },
  setup() {
    return {
    };
  },
});
</script>


<template>
  <UMDAnnotation
    v-if="!['changepoint', 'remediation'].includes(mode)"
    :mode="mode"
  />
  <UMDChangepoint
    v-else-if="mode ==='changepoint'"
    :mode="mode"
  />
  <UMDRemediation
    v-else-if="mode ==='remediation'"
    :mode="mode"
  />
</template>

<style scoped lang="scss">
</style>
