<script lang="ts">
import {
  computed, defineComponent, ref, Ref, watch,
} from '@vue/composition-api';

import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import { replace } from 'lodash';
import { useGirderRest } from 'platform/web-girder/plugins/girder';
import {
  useCameraStore,
  useHandler,
  useSelectedTrackId,
  useTime,
} from 'vue-media-annotator/provides';

export default defineComponent({
  name: 'UMDAnnotation',

  components: {
    StackedVirtualSidebarContainer,

  },

  props: {
    width: {
      type: Number,
      default: 500,
    },
  },

  setup() {
    const selectedTrackIdRef = useSelectedTrackId();

    const { frame } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();
    const arousal = ref(0);
    const valence = ref(0);
    const baseEmotionsList = ['Anger', 'Anticipation', 'Joy', 'Trust', 'Fear', 'Surprise', 'Sadness', 'Disgust'];
    const emotionsAdhered: Ref<string[]> = ref([]);
    const emotionsNotAdhered: Ref<string[]> = ref([]);
    const normList = ref([]);
    const changePointFrame = ref(-1);
    const changePointImpact = ref(0);
    const changePointComment = ref('');
    const userLogin = ref('');
    const adheredEmotionsList = computed(() => (
      baseEmotionsList.filter((item) => !emotionsNotAdhered.value.includes(item))));
    const notAdheredEmotionsList = computed(() => (
      baseEmotionsList.filter((item) => !emotionsAdhered.value.includes(item))));

    const checkAttributes = (trackNum: number | null, loadValues = false) => {
      // load existing attributes
      let hasAttributes = false;
      if (trackNum !== null) {
        const track = cameraStore.getAnyTrack(trackNum);
        Object.keys(track.attributes).forEach((key) => {
          if (key.includes(userLogin.value)) {
            hasAttributes = true;
            if (loadValues) {
              const replaced = key.replace(`${userLogin.value}_`, '');
              if (replaced === 'Valence') {
                valence.value = track.attributes[key] as number;
              }
              if (replaced === 'Arousal') {
                arousal.value = track.attributes[key] as number;
              }
              if (replaced === 'AdheredEmotions') {
                emotionsAdhered.value = (track.attributes[key] as string).split('_');
              }
              if (replaced === 'NotAdheredEmotions') {
                emotionsNotAdhered.value = (track.attributes[key] as string).split('_');
              }
            }
          }
        });
        if (loadValues) {
          track.features.forEach((feature) => {
            const currentFrame = feature.frame;
            if (feature.attributes) {
              Object.keys(feature.attributes).forEach((key) => {
                if (key.includes(userLogin.value) && feature.attributes) {
                  const attribute = feature.attributes[key];
                  const replaced = key.replace(`${userLogin.value}_`, '');
                  if (replaced === 'Impact') {
                    changePointImpact.value = attribute as number;
                    changePointFrame.value = currentFrame;
                  }
                  if (replaced === 'Comment') {
                    changePointComment.value = attribute as string;
                    changePointFrame.value = currentFrame;
                  }
                }
              });
            }
          });
          if (loadValues) {
            handler.trackSeek(track.begin);
          }
        }
      }
      return hasAttributes;
    };

    const initialize = async () => {
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        handler.trackSelect(0, false);
        checkAttributes(0);
      }
    };
    initialize();
    checkAttributes(selectedTrackIdRef.value, true);
    watch(selectedTrackIdRef, () => {
      checkAttributes(selectedTrackIdRef.value, true);
    });

    const setCheckpoint = () => {
      changePointFrame.value = frame.value;
    };

    const hasPrevious = computed(() => (
      selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0));

    const hasNext = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        return checkAttributes(selectedTrackIdRef.value);
      }
      return false;
    });

    const submit = () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        // Set attributes;
        track.setAttribute(`${userLogin.value}_Valence`, valence.value);
        track.setAttribute(`${userLogin.value}_Arousal`, arousal.value);
        track.setAttribute(`${userLogin.value}_AdheredEmotions`, emotionsAdhered.value.join('_'));
        track.setAttribute(`${userLogin.value}_NotAdheredEmotions`, emotionsNotAdhered.value.join('_'));
        // set Change Point Information
        if (changePointFrame.value !== -1) {
          if (track.getFeature(changePointFrame.value)[0] === null
          || !track.getFeature(changePointFrame.value)[0]?.keyframe) {
            track.toggleKeyframe(changePointFrame.value);
          }
          track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Impact`, changePointImpact.value);
          track.setFeatureAttribute(changePointFrame.value, `${userLogin.value}_Comment`, changePointComment.value);
        }
        // save the file
        handler.save();
        const oldTrackNum = selectedTrackIdRef.value;
        handler.trackSelectNext(1);
        if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value !== oldTrackNum) {
          arousal.value = 0;
          valence.value = 0;
          emotionsAdhered.value = [];
          emotionsNotAdhered.value = [];
          changePointFrame.value = -1;
          changePointImpact.value = 0;
          changePointComment.value = '';
        }
      }
    };
    const goToChangePoint = () => {
      //Need to set this up
    };
    const changeTrack = (direction: -1 | 1) => {
      arousal.value = 0;
      valence.value = 0;
      emotionsAdhered.value = [];
      emotionsNotAdhered.value = [];
      changePointFrame.value = -1;
      changePointImpact.value = 0;
      changePointComment.value = '';

      handler.trackSelectNext(direction);
    };
    return {
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      arousal,
      valence,
      adheredEmotionsList,
      notAdheredEmotionsList,
      emotionsAdhered,
      emotionsNotAdhered,
      frame,
      changePointFrame,
      changePointImpact,
      changePointComment,
      setCheckpoint,
      submit,
      goToChangePoint,
      changeTrack,
    };
  },
});
</script>


<template>
  <StackedVirtualSidebarContainer
    :width="width"
    :enable-slot="false"
  >
    <template>
      <v-container>
        <v-row dense>
          <h2>Segment {{ selectedTrackIdRef }}</h2>
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
        <p>
          Some instruction text to indicate to the annotator what to do.
          This could be lengthy to provide more detailed instructions or not.
        </p>
        <v-row>
          <v-col>
            <v-slider
              v-model="arousal"
              label="Arousal"
              min="1"
              max="1000"
              step="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-slider
              v-model="valence"
              label="Valence"
              min="1"
              max="1000"
              step="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="emotionsAdhered"
              :items="adheredEmotionsList"
              chips
              label="Emotions Adhered To"
              multiple
              solo
              clearable
              persistent-hint
              deletable-chips
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="emotionsNotAdhered"
              :items="notAdheredEmotionsList"
              chips
              label="Emotions Not Adhered To"
              multiple
              solo
              clearable
              persistent-hint
              deletable-chips
            />
          </v-col>
        </v-row>
        <v-row v-if="(changePointFrame == -1)">
          <v-btn @click="setCheckpoint">
            Set CheckPoint {{ frame }}
          </v-btn>
        </v-row>
        <div v-if="(changePointFrame != -1)">
          <v-row>
            <v-btn @click="setCheckpoint">
              Set Changepoint to {{ frame }}
            </v-btn>
          </v-row>
          <h4> Current ChangePoint : {{ changePointFrame }}</h4>
          <v-btn @click="goToChangePoint">
            Go to ChangePoint
          </v-btn>
          <v-row>
            <v-col>
              <v-slider
                v-model="changePointImpact"
                label="Impact"
                min="1"
                max="5"
                step="1"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea
                v-model="changePointComment"
                outlined
                label="Comment"
              />
            </v-col>
          </v-row>
        </div>
        <v-row v-if="(changePointFrame != -1)">
          <v-col>
            <v-btn
              color="success"
              @click="submit"
            >
              Submit
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </template>
  </StackedVirtualSidebarContainer>
</template>
