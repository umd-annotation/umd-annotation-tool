<script lang="ts">
import {
  computed, defineComponent, ref, Ref, watch, PropType, onMounted, nextTick,
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
import UMDTA2Translation, { TA2Translation } from './UMDTA2Translation.vue';



export default defineComponent({
  name: 'UMDTA2Annotation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
    UMDTA2Translation,
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

  setup(props, { emit }) {
    const selectedTrackIdRef = useSelectedTrackId();

    const { prompt } = usePrompt();
    const { frame, maxSegment } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();

    const alreadyAnnotated = ref(false);

    const translationData: Ref<TA2Translation | null> = ref(null);

    const activePanel = ref(0);

    const normsSelected: Ref<string[]> = ref([]);
    const baseNormsList = computed(() => {
      if (normsSelected.value.includes('None')) {
        return ['None'];
      }
      const root = [
        'Admiration',
        'Apology',
        'Criticism',
        'Finalizing Negotiating/Deal',
        'Greeting',
        'Persuasion',
        'Refusing a Request',
        'Request',
        'Taking Leave',
        'Thanks',
      ];
      const normVariants = root
        .map((item) => [`${item} (adhered)`, `${item} (violated)`])
        .reduce((acc, x) => acc.concat(x)).sort();

      return [
        'None',
        ...normVariants,
      ];
    });
    const userLogin = ref('');
    const loadedAttributes = ref(false);

    let framePlaying = -1;
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
        framePlaying = track.end;
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
        };
        const transKeys = Object.keys(transObject);
        Object.keys(track.attributes).forEach((key) => {
          // Grab Translation root data
          if (transKeys.includes(key)) {
            transObject[key] = track.attributes[key];
          }
          if (key.includes(userLogin.value)) {
            const replaced = key.replace(`${userLogin.value}_`, '');
            if (replaced === 'Valence' && props.mode === 'VAE') {
              if (loadValues) {
                console.log('where we load data for attributes');
              }
              hasAttributes = true;
            }
            if (replaced === 'Norms' && props.mode === 'norms') {
              if (loadValues) {
                // Norms saving
                /*
                normsObject.value = (track.attributes[key] as NormsObjectValues);
                normsSelected.value = [];
                Object.entries(normsObject.value).forEach(([normKey, val]) => {
                  const adhered = `${normKey} (adhered)`;
                  const violated = `${normKey} (violated)`;
                  if (val.includes('adhered')) {
                    normsSelected.value.push(adhered);
                  }
                  if (val.includes('violated')) {
                    normsSelected.value.push(violated);
                  }
                  if (val.includes('noann') || val.includes('EMPTY_NA')) {
                    normsSelected.value.push('None');
                  }
                });
                */
              }
              hasAttributes = true;
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
      if (track === undefined) {
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
      handler.setMaxSegment(0);
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        getMaxSegmentAnnotated();
      }
    };
    onMounted(() => initialize());
    loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
    watch(selectedTrackIdRef, () => {
      loadedAttributes.value = checkAttributes(selectedTrackIdRef.value, true);
      if (selectedTrackIdRef.value === maxSegment.value && !loadedAttributes.value) {
        console.log('reloading datastore');
      }
      if (selectedTrackIdRef.value !== null) {
        handler.setMaxSegment(selectedTrackIdRef.value);
      }
    });


    const hasPrevious = computed(() => (
      selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0));

    const hasNext = computed(() => {
      if (props.mode === 'review') {
        return true;
      }
      if (selectedTrackIdRef.value !== null) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value + 1);
        if (newTrack) {
          return checkAttributes(selectedTrackIdRef.value);
        }
        return false;
      }
      return false;
    });

    const submit = async () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getPossibleTrack(selectedTrackIdRef.value);
        // Set attributes;
        if (track === undefined) {
          return;
        }
        if (props.mode === 'norms' || props.mode === 'review') {
          // Seting Norms value
          //track.setAttribute(`${userLogin.value}_Norms`, normsObject.value);
        }
        // save the file
        handler.save();
        const oldTrackNum = selectedTrackIdRef.value;
        const newTrack = cameraStore.getAnyPossibleTrack(oldTrackNum + 1);
        if (newTrack) {
          handler.trackSelectNext(1, true);
        } else {
          alreadyAnnotated.value = true;
        }
        if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value !== oldTrackNum) {
          await nextTick();
        }
      }
    };
    const changeTrack = (direction: -1 | 1) => {
      if (selectedTrackIdRef.value === maxSegment.value) {
        if (props.mode === 'norms') {
          // Norms data
          //dataStore.normsSelected = normsSelected.value;
          //dataStore.normsObject = normsObject.value;
        }
      }
      handler.trackSelectNext(direction, true);
    };

    // const syncNorms = (data: string[]) => {
    //   const keys = Object.keys(normsObject.value);
    //   for (let i = 0; i < keys.length; i += 1) {
    //     if (!normsSelected.value.includes(keys[i])) {
    //       delete normsObject.value[keys[i]];
    //     }
    //   }
    //   if (data.includes('None')) {
    //     normsObject.value.None = 'EMPTY_NA';
    //   } else {
    //     for (let i = 0; i < data.length; i += 1) {
    //       let adhered = data[i].includes('(adhered)');
    //       let violated = data[i].includes('(violated)');
    //       const baseKey = data[i].replace('(adhered)', '').replace('(violated)', '').trim();
    //       if (normsObject.value[baseKey]) {
    //         const existing = normsObject.value[baseKey];
    //         if (existing === 'adhered') {
    //           adhered = true;
    //         }
    //         if (existing === 'violated') {
    //           violated = true;
    //         }
    //       }
    //       if (adhered && violated) {
    //         normsObject.value[baseKey] = 'adhered_violated';
    //       } else if (adhered) {
    //         normsObject.value[baseKey] = 'adhered';
    //       } else if (violated) {
    //         normsObject.value[baseKey] = 'violated';
    //       }
    //     }
    //   }
    // };

    watch(() => frame.value, () => {
      if (framePlaying !== -1 && frame.value >= framePlaying) {
        handler.pausePlayback();
        framePlaying = -1;
      }
      if (frame.value > (150 + (maxSegment.value + 2) * 450)) {
        handler.pausePlayback();
        if (selectedTrackIdRef.value !== null) {
          const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
          if (track) {
            handler.seekToFrame(150 + (maxSegment.value + 2) * 450);
          }
        }
      }
    });

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

    const submitValid = computed(() => {
      if (props.mode === 'norms') {
        return normsValid.value;
      }
      return false;
    });

    return {
      alreadyAnnotated,
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      baseNormsList,
      normsSelected,
      frame,
      outsideSegment,
      loadedAttributes,
      normsValid,
      submitValid,
      submit,
      changeTrack,
      seekBegin,
      seekEnd,
      playSegment,
      translationData,
      activePanel,
      //refs
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
          Segment {{ selectedTrackIdRef }}
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
        <v-expansion-panel>
          <v-expansion-panel-header><h3>Information</h3></v-expansion-panel-header>
          <v-expansion-panel-content>
            <UMDTA2Translation
              v-if="translationData"
              :data="translationData"
            />
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-row>
        <v-col>
          <v-btn
            :color="loadedAttributes ? 'warning' : 'success'"
            :disabled="outsideSegment || !submitValid"
            @click="submit"
          >
            {{ loadedAttributes ? 'Update' : 'Submit' }}
          </v-btn>
        </v-col>
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
