<script lang="ts">
import {
  defineComponent, PropType,
} from '@vue/composition-api';
import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import UMDAnnotation from './UMDAnnotation.vue';
import UMDChangepoint from './UMDChangepoint.vue';
import UMDRemediation from './UMDRemediation.vue';
import UMDTA2Annotation from './UMDTA2Annotation.vue';

export default defineComponent({
  name: 'UMDAnnotationWrapper',
  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDAnnotation,
    UMDChangepoint,
    UMDRemediation,
    UMDTA2Annotation,
  },
  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String as PropType<'VAE' | 'norms' | 'changepoint' | 'emotion' | 'remediation' | 'review' | 'TA2Annotation'>,
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
    v-if="!['changepoint', 'remediation', 'TA2Annotation'].includes(mode)"
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
  <UMDTA2Annotation
    v-else-if="mode === 'TA2Annotation'"
  />
</template>

<style scoped lang="scss">
</style>
