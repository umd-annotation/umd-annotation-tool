<script lang="ts">
import {
  defineComponent, PropType,
} from '@vue/composition-api';
import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import { UMDAnnotationMode } from 'platform/web-girder/store/types';
import UMDAnnotation from './UMDAnnotation.vue';
import UMDChangepoint from './UMDChangepoint.vue';
import UMDRemediation from './UMDRemediation.vue';
import UMDTA2Annotation from './UMDTA2Annotation.vue';
import UMDTA2AnnotationCreator from './UMDTA2AnnotationCreator.vue';

export default defineComponent({
  name: 'UMDAnnotationWrapper',
  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDAnnotation,
    UMDChangepoint,
    UMDRemediation,
    UMDTA2Annotation,
    UMDTA2AnnotationCreator,
  },
  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String as PropType<UMDAnnotationMode>,
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
    v-if="!['changepoint', 'remediation'].includes(mode) && !mode.includes('TA2Annotation')"
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
  <UMDTA2AnnotationCreator
    v-else-if="mode.includes('TA2Annotation_Creation')"
    :mode="mode"
  />

  <UMDTA2Annotation
    v-else-if="mode.includes('TA2Annotation')"
    :mode="mode"
  />
</template>

<style scoped lang="scss">
</style>
