<script lang="ts">
import {
  defineComponent,
} from '@vue/composition-api';
import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import UMDTA2Annotation from './UMDTA2Annotation.vue';

export default defineComponent({
  name: 'UMDTA2AnnotationWrapper',
  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDTA2Annotation,
  },
  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      default: 'review',
    },
    name: {
      type: String,
      default: undefined,
    },
  },
  setup() {
    return {
    };
  },
});
</script>


<template>
  <UMDTA2Annotation />
</template>

<style scoped lang="scss">
</style>
