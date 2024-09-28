<script lang="ts">
import {
  computed, defineComponent, ref, Ref, watch, PropType, onMounted,
} from '@vue/composition-api';

import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import { useGirderRest } from 'platform/web-girder/plugins/girder';
import {
  useCameraStore,
  useHandler,
  useSelectedTrackId,
  useTime,
} from 'vue-media-annotator/provides';
import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import { UMDAnnotationMode } from 'platform/web-girder/store/types';
import UMDTA2Translation, { TA2Translation } from './UMDTA2Translation.vue';
import UMDTA2AnnotationWizard, { TA2Annotation } from './UMDTA2AnnotationWizard.vue';


export default defineComponent({
  name: 'UMDTA2Annotation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDTA2Translation,
    UMDTA2AnnotationWizard,
  },

  props: {
    width: {
      type: Number,
      default: 500,
    },
    mode: {
      type: String as PropType<UMDAnnotationMode>,
      default: 'TA2Annotation_ASRMTQuality',
    },
    name: {
      type: String,
      default: undefined,
    },
  },

  setup(props, { emit }) {
    const selectedTrackIdRef = useSelectedTrackId();

    const { prompt } = usePrompt();
    const { frame } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();

    const alreadyAnnotated = ref(false);

    const translationData: Ref<TA2Translation | null> = ref(null);

    const activePanel = ref(0);

    const userLogin = ref('');
    const loadedAttributes = ref(false);
    const annotation: Ref<TA2Annotation | null> = ref({});

    const LCName = computed(() => {
      if (props.name) {
        if (props.name.includes('LC1')) {
          return 'LC1';
        }
        if (props.name.includes('LC2')) {
          return 'LC2';
        }
        if (props.name.includes('LC2')) {
          return 'LC1';
        }
        if (props.name.includes('LC3')) {
          return 'LC3';
        }
      }
      return 'LC1';
    });
    const seekBegin = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.seekToFrame(track.begin);
      }
    };
    const seekEnd = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.seekToFrame(track.end);
      }
    };
    const playSegment = () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        handler.replayFromFrame(track.begin);
      }
    };

    const checkAttributes = (trackNum: number | null, loadValues = false) => {
      // load existing attributes
      let hasAttributes = false;
      if (trackNum !== null) {
        const track = cameraStore.getAnyPossibleTrack(trackNum);
        if (track === undefined) {
          return false;
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const transObject: Record<string, null | any> = {
          translation: null,
          ASRText: null,
          speaker: null,
          sourceLanguage: null,
          targetLanguage: null,
          alerts: null,
          rephrase: null,
          // eslint-disable-next-line @typescript-eslint/camelcase
          rephrase_translation: null,
        };
        const transKeys = Object.keys(transObject);
        annotation.value = { };
        Object.keys(track.attributes).forEach((key) => {
          // Grab Translation root data
          if (transKeys.includes(key)) {
            transObject[key] = track.attributes[key];
          }
          if (key.includes(`${userLogin.value}_`) && annotation.value) { // Get User Attributes
            const replaced = key.replace(`${userLogin.value}_`, '');
            if (replaced === 'ASRQuality') {
              if (loadValues) {
                annotation.value.ASRQuality = track.attributes[key] as number;
              }
              if (props.mode === 'TA2Annotation_ASRMTQuality') {
                hasAttributes = true;
              }
            }
            if (replaced === 'MTQuality') {
              if (loadValues) {
                annotation.value.MTQuality = track.attributes[key] as number;
              }
              if (props.mode === 'TA2Annotation_ASRMTQuality' || props.mode === 'TA2Annotation_MTQuality') {
                hasAttributes = true;
              }
            }
            if (replaced === 'AlertsQuality') {
              if (loadValues) {
                annotation.value.AlertsQuality = track.attributes[key] as number;
              }
              if (props.mode === 'TA2Annotation_Remediation') {
                hasAttributes = true;
              }
            }
            if (replaced === 'RephrasingQuality') {
              if (loadValues) {
                annotation.value.RephrasingQuality = track.attributes[key] as number;
              }
              if (props.mode === 'TA2Annotation_Remediation') {
                hasAttributes = true;
              }
            }
            if (replaced === 'DelayedRemediation') {
              if (loadValues) {
                annotation.value.DelayedRemediation = track.attributes[key] as boolean;
              }
              if (props.mode === 'TA2Annotation_Remediation') {
                hasAttributes = true;
              }
            }
            if (replaced === 'TA2Norms') {
              if (loadValues) {
                annotation.value.Norms = (track.attributes[key] as TA2Annotation['Norms']);
              }
              if (props.mode === 'TA2Annotation_Norms') {
                hasAttributes = true;
              }
            }
          }
        });
        // TODO Double check this type setting
        translationData.value = transObject as unknown as TA2Translation;
        if (loadValues) {
          emit('seek', track.begin);
        }
      }
      return hasAttributes;
    };

    const getMaxSegmentAnnotated = async () => {
      const Ids = cameraStore.camMap.value.get('singleCam')?.trackStore.annotationIds.value;
      let maxId = -1;
      if (Ids) {
        for (let i = 0; i < Ids?.length; i += 1) {
          const val = checkAttributes(i);
          if (val) {
            maxId = i;
          }
        }
      }
      const track = cameraStore.getAnyPossibleTrack(maxId + 1);
      if (track === undefined && maxId !== -1) {
        // We are at max segment
        const text = 'You have already fully annotated this video. You can choose to edit or re-do these annotations, but you should do so with caution, and generally only if you have been instructed to.';
        const res = await prompt({
          title: 'Video already annotated!',
          text,
          alert: 'warning',
          positiveButton: 'Edit anyway',
          confirm: true,
        });
        if (res) {
          handler.trackSelect(0, false);
        } else {
          alreadyAnnotated.value = true;
        }
      } else {
        handler.trackSelect(maxId + 1, false);
      }
      loadedAttributes.value = checkAttributes(maxId + 1, true);
      seekBegin();
    };
    const initialize = async () => {
      handler.setMaxSegment(99999);
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        getMaxSegmentAnnotated();
      }
      loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
    };
    onMounted(() => initialize());
    watch(selectedTrackIdRef, () => {
      loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
    });


    const hasPrevious = computed(() => (
      selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0));

    const hasNext = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value + 1);
        if (newTrack) {
          return true;
        }
        return false;
      }
      return false;
    });

    const submit = async (data: TA2Annotation) => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getPossibleTrack(selectedTrackIdRef.value);
        // Set attributes;
        if (track === undefined) {
          return;
        }
        if (data.ASRQuality !== undefined) {
          track.setAttribute(`${userLogin.value}_ASRQuality`, data.ASRQuality);
        }
        if (data.MTQuality !== undefined) {
          track.setAttribute(`${userLogin.value}_MTQuality`, data.MTQuality);
        }
        if (data.AlertsQuality !== undefined) {
          track.setAttribute(`${userLogin.value}_AlertsQuality`, data.AlertsQuality);
        }
        if (data.RephrasingQuality !== undefined) {
          track.setAttribute(`${userLogin.value}_RephrasingQuality`, data.RephrasingQuality);
        }
        if (data.DelayedRemediation !== undefined) {
          track.setAttribute(`${userLogin.value}_DelayedRemediation`, data.DelayedRemediation);
        }
        if (data.Norms !== undefined) {
          track.setAttribute(`${userLogin.value}_TA2Norms`, data.Norms);
        }
        // save the file
        handler.save();
        if (selectedTrackIdRef.value + 1 >= cameraStore.sortedTracks.value.length) { // Done and we sohuld indicate to the user that they are finished
          await prompt({
            title: 'Completed',
            text: 'You have completed Annotating this video and the last turn saved.',
            positiveButton: 'Confirm',
            confirm: false,
          });
        }
      }
    };
    const changeTrack = (direction: -1 | 1) => {
      handler.trackSelectNext(direction, true);
      checkAttributes(selectedTrackIdRef.value);
    };

    const outsideSegment = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (frame.value > track.end || frame.value < track.begin) {
          return true;
        }
        return false;
      }
      return true;
    });

    const normsValid = ref(false);

    return {
      alreadyAnnotated,
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      frame,
      outsideSegment,
      loadedAttributes,
      normsValid,
      submit,
      changeTrack,
      seekBegin,
      seekEnd,
      playSegment,
      translationData,
      activePanel,
      //refs
      annotation,
      LCName,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <div v-if="!alreadyAnnotated">
      <v-row
        dense
        class="scroll-sticky"
      >
        <h2 class="mr-4 mt-1">
          Turn {{ (selectedTrackIdRef || 0) + 1 }}
        </h2>
        <div class="ml-2 mt-2">
          <tooltip-btn
            small
            icon="mdi-skip-previous"
            tooltip-text="Seek to first frame of segment"
            @click="seekBegin"
          />
          <tooltip-btn
            small
            icon="mdi-replay"
            tooltip-text="Playback current Segment"
            @click="playSegment"
          />
          <tooltip-btn
            small
            icon="mdi-skip-next"
            tooltip-text="Seek to end of the frame"
            @click="seekEnd"
          />
        </div>
        <v-spacer />
        <v-btn
          color="primary"
          :disabled="!hasPrevious"
          class="mx-2"
          @click="changeTrack(-1)"
        >
          Prev
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!hasNext"
          class="mx-2"
          @click="changeTrack(1)"
        >
          Next
        </v-btn>
      </v-row>
      <v-expansion-panels v-model="activePanel">
        <v-expansion-panel style="border: 1px solid white">
          <v-expansion-panel-header><h3>Translation</h3></v-expansion-panel-header>
          <v-expansion-panel-content>
            <UMDTA2Translation
              v-if="translationData"
              :data="translationData"
            />
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-row v-if="loadedAttributes || annotation">
        <UMDTA2AnnotationWizard
          :annotations="annotation"
          :outside-segment="outsideSegment"
          :translation="translationData"
          :l-c="LCName"
          :mode="mode"
          :name="name"
          @save="submit($event)"
          @next-turn="changeTrack(1)"
        />
      </v-row>
      <v-row>
        <v-alert
          v-if="(outsideSegment)"
          outlined
          dense
          type="warning"
          class="mx-3"
        >
          Outside Current segment.  Return to the segment to submit or update.
          <v-btn
            color="primary"
            @click="seekBegin()"
          >
            Return to Segment
          </v-btn>
        </v-alert>
      </v-row>
    </div>
    <div v-else>
      <h3> Video Completed</h3>
    </div>
  </v-container>
</template>

<style scoped lang="scss">
.scroll-sticky {
  z-index: 99;
  position: -webkit-sticky; /* Safari */
  position: sticky;
  top: 0px;
  background-color: rgb(30, 30, 30);
}
.valencegradient {
  background: rgb(255,255,255);
  background: radial-gradient(circle, rgba(166, 166, 166, 1) 0%, rgba(0,0,0,1) 100%);
  clip-path: polygon(0 0, 0 100%, 50% 50%, 100% 100%, 100% 0, 50% 50%);

}
.arrousalgradient{
  background: rgb(255,255,255);
  background: linear-gradient(90deg, rgb(166, 166, 166) 0%, rgba(0,0,0,1) 100%);
  clip-path: polygon(100% 0, 0 50%, 100% 100%);
}
.maincontainer {
  font-size: 1.2em !important;
}
.emoji {
  font-size: 1.75em;
  font-family: 'Noto Color Emoji';

}
.bottomborder{
  border-bottom: 3px solid gray;
}
.v-sheet.v-list {
  background-color: rgb(76, 76, 76);
  font-weight: bolder;
}
</style>
