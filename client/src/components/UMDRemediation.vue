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

export default defineComponent({
  name: 'UMDRemediation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
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
    const selectedTrackIdRef = useSelectedTrackId();

    const { frame, maxFrame } = useTime();
    const handler = useHandler();
    const restClient = useGirderRest();
    const cameraStore = useCameraStore();
    const remediationFrame = ref(-1);
    const remediationComment = ref('');
    const userLogin = ref('');
    const loadedAttributes = ref(false);
    const remediations: Ref<{frame: number; comment: string}[]> = ref([]);
    const selectedRemediation: Ref<number | null> = ref(null);
    const enableCompleteButton = ref(false);
    const alreadyComplete = ref(false);

    const checkAttributes = () => {
      // load existing attributes
      remediations.value = [];
      let hasAttributes = false;
      const store = cameraStore.camMap.value.get('singleCam');
      if (store) {
        // eslint-disable-next-line no-unused-expressions
        store?.trackStore.annotationMap.forEach((track) => {
          if (track.attributes) {
            Object.entries(track.attributes).forEach(([key, item]) => {
              if (key.includes(userLogin.value)) {
                const replaced = key.replace(`${userLogin.value}_`, '');
                if (replaced === 'RemediationComplete' && item) {
                  alreadyComplete.value = true;
                  handler.setMaxSegment(track.id);
                }
              }
            });
          }

          track.features.forEach((feature) => {
            const currentFrame = feature.frame;
            if (feature.attributes) {
              let foundFeature = false;
              Object.keys(feature.attributes).forEach((key) => {
                if (key.includes(userLogin.value) && feature.attributes) {
                  hasAttributes = true;
                  const attribute = feature.attributes[key];
                  const replaced = key.replace(`${userLogin.value}_`, '');
                  if (replaced === 'RemediationComment') {
                    remediationComment.value = attribute as string;
                    remediationFrame.value = currentFrame;
                    foundFeature = true;
                  }
                }
              });
              if (foundFeature) {
                remediations.value.push({
                  frame: remediationFrame.value,
                  comment: remediationComment.value,
                });
                const segment = Math.floor((currentFrame - 150) / 450);
                handler.setMaxSegment(segment);
              }
            }
          });
        });
      }
      return hasAttributes;
    };

    const initialize = async () => {
      handler.setMaxSegment(0);
      const user = await restClient.fetchUser();
      userLogin.value = user.login;
      if (selectedTrackIdRef.value === null) {
        handler.trackSelectNext(1, true);
        loadedAttributes.value = checkAttributes();
      }
    };
    onMounted(() => initialize());

    watch(frame, () => {
      // Determine which track we are in
      if (frame.value - 150 > 0) {
        const segment = Math.floor((frame.value - 150) / 450);
        if (selectedTrackIdRef.value !== segment) {
          handler.trackSelect(segment, false);
        }
      }
      if (maxFrame.value > 0 && maxFrame.value - frame.value < 30) {
        // Show submit button to complete data
        enableCompleteButton.value = true;
      } else {
        enableCompleteButton.value = false;
      }
    });


    const setRemediation = () => {
      remediationFrame.value = frame.value;
    };

    const existingFrames = computed(() => remediations.value.map((item) => item.frame));

    const deleteRemediation = async (index: number, save = true) => {
      const changeData = remediations.value[index];
      const segment = Math.floor((changeData.frame - 150) / 450);
      const track = cameraStore.getAnyTrack(segment);
      if (track) {
        if (track.getFeature(changeData.frame)[0]) {
          track.removeFeatureAttribute(changeData.frame, `${userLogin.value}_RemediationComment`);
        }
        if (selectedRemediation.value === index) {
          selectedRemediation.value = null;
        }
        if (save) {
          await handler.save();
          checkAttributes();
        }
      }
    };

    const addRemediation = (internal = false) => {
      remediations.value.push({
        frame: frame.value,
        comment: '',
      });
      if (!internal) {
        handler.pausePlayback();
      }
      remediations.value.sort((a, b) => a.frame - b.frame);
      const foundIndex = remediations.value.findIndex((item) => item.frame === frame.value);
      remediationFrame.value = frame.value;
      remediationComment.value = '';
      selectedRemediation.value = foundIndex;
    };

    const submit = async () => {
      // Need to get information and set it for the track attributes
      if (selectedTrackIdRef.value !== null && selectedRemediation.value !== null) {
        if (remediations.value[selectedRemediation.value].frame !== remediationFrame.value) {
          const comment = remediationComment.value;
          deleteRemediation(selectedRemediation.value, false);
          addRemediation(true);
          remediationComment.value = comment;
        }
        const segment = Math.floor((remediationFrame.value - 150) / 450);
        const track = cameraStore.getAnyTrack(segment);
        // Set attributes;
        // set Change Point Information
        if (remediationFrame.value !== -1) {
          if (track.getFeature(remediationFrame.value)[0] === null
          || !track.getFeature(remediationFrame.value)[0]?.keyframe) {
            track.toggleKeyframe(remediationFrame.value);
          }
          track.setFeatureAttribute(remediationFrame.value, `${userLogin.value}_RemediationComment`, remediationComment.value);
        }
        // save the file
        selectedRemediation.value = null;
        handler.save();
        checkAttributes();
      }
    };


    const frameToTime = (frameNum: number) => {
      const totalSeconds = (1 / 30) * frameNum;
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = Math.floor(totalSeconds % 3600 % 60);
      if (hours > 0) {
        return `${hours}:${minutes}:${seconds}`;
      }
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    const goToRemediation = (frameNum: number) => {
      //Need to set this up
      handler.pausePlayback();
      handler.seekToFrame(frameNum);
      selectedRemediation.value = null;
    };
    const changeTrack = (direction: -1 | 1) => {
      remediationFrame.value = -1;
      remediationComment.value = '';

      handler.trackSelectNext(direction, true);
    };

    const editRemediation = (index: number) => {
      if (selectedRemediation.value === index) {
        selectedRemediation.value = null;
        return;
      }
      selectedRemediation.value = index;
      remediationFrame.value = remediations.value[index].frame;
      remediationComment.value = remediations.value[index].comment;
    };

    const submitValid = ref(false);

    const completeVideo = async () => {
      const segment = Math.floor((frame.value - 151) / 450);
      const track = cameraStore.getAnyTrack(segment);
      // Set attributes;
      // set Change Point Information
      if (track !== undefined) {
        track.setAttribute(`${userLogin.value}_RemediationComplete`, true);
      }
      handler.save();
      checkAttributes();
    };

    return {
      selectedTrackIdRef,
      frame,
      remediationFrame,
      remediationComment,
      loadedAttributes,
      remediations,
      selectedRemediation,
      existingFrames,
      submitValid,
      enableCompleteButton,
      alreadyComplete,
      completeVideo,
      setRemediation,
      submit,
      goToRemediation,
      changeTrack,
      editRemediation,
      frameToTime,
      deleteRemediation,
      addRemediation,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <v-row dense>
      <v-col cols="11">
        <h3>
          Remediations
        </h3>
      </v-col>
      <v-col>
        <v-tooltip
          open-delay="200"
          left
          max-width="300"
        >
          <template #activator="{ on }">
            <v-icon
              v-on="on"
            >
              mdi-help
            </v-icon>
          </template>
          <p style="font-size:1.4em">
            Indicate where the interpreter applied remediation of any kind (timestamps).
            Add a comment explaining the type of remediation.
          </p>
        </v-tooltip>
      </v-col>
    </v-row>
    <v-row v-if="alreadyComplete">
      <p class="pa-2">
        This Video is marked as complete and has been
        annotated even if no remediation annotations exist.
        <br>
        You may modify the remnediation if necessary.
      </p>
    </v-row>

    <v-btn
      :disabled="existingFrames.includes(frame)"
      color="success"
      @click="addRemediation()"
    >
      Add Remediation at {{ frameToTime(frame) }}
    </v-btn>
    <v-card style="max-height:30vh; overflow-y:scroll">
      <v-list>
        <v-list-item
          v-for="(item, index) in remediations"
          :key="`${index}_${item.frame}`"
          :class="{selected: selectedRemediation === index}"
        >
          <v-row>
            <v-col cols="2">
              <v-chip
                class="px-2"
                @click="goToRemediation(item.frame)"
              >
                {{ frameToTime(item.frame) }}
              </v-chip>
            </v-col>
            <v-col>
              <v-tooltip
                open-delay="100"
                bottom
              >
                <template #activator="{ on }">
                  <div
                    class="comment"
                    v-on="on"
                  >
                    {{ item.comment }}
                  </div>
                </template>
                <span
                  class="ma-0 pa-1"
                >
                  {{ item.comment }}
                </span>
              </v-tooltip>
            </v-col>
            <v-col cols="1">
              <v-icon @click="editRemediation(index)">
                mdi-pencil
              </v-icon>
            </v-col>
            <v-col cols="1">
              <v-icon
                color="error"
                @click="deleteRemediation(index)"
              >
                mdi-delete
              </v-icon>
            </v-col>
          </v-row>
        </v-list-item>
      </v-list>
    </v-card>
    <div v-if="selectedRemediation !== null">
      <v-row v-if="(remediationFrame == -1)">
        <v-btn
          @click="setRemediation"
        >
          Set Remediation {{ frame }}
        </v-btn>
      </v-row>
      <div v-if="(remediationFrame != -1)">
        <h4> Current Remediation : {{ frameToTime(remediationFrame) }}</h4>
        <v-row class="mt-2 ml-2">
          <v-btn
            v-if="(frame !== remediationFrame)"
            outlined
            :disabled="existingFrames.includes(frame)"
            @click="setRemediation()"
          >
            Set Remediation to current time: {{ frameToTime(frame) }}
          </v-btn>
        </v-row>
        <v-row>
          <v-col>
            <v-form v-model="submitValid">
              <v-textarea
                v-model="remediationComment"
                outlined
                :rules="[v => v.length > 0 || 'Comment is required']"
                required
                label="Comment"
              />
            </v-form>
          </v-col>
        </v-row>
      </div>
    </div>
    <v-row>
      <v-btn
        v-if="selectedRemediation !== null"
        color="warning"
        class="mx-2"
        :disabled="!submitValid"
        @click="submit"
      >
        Save
      </v-btn>
    </v-row>
    <v-row
      v-if="!alreadyComplete"
      dense
      style="position:absolute;bottom:10px"
    >
      <p
        v-if="!alreadyComplete"
        class="pa-2"
      >
        Once the dataset has been viewed completely.
        The Complete button below will be enabled to submit.
      </p>
      <v-btn
        color="success"
        class="mx-2"
        :disabled="!enableCompleteButton || alreadyComplete"
        @click="completeVideo"
      >
        Complete
      </v-btn>
    </v-row>
  </v-container>
</template>

<style lang="scss">
.scroll-sticky {
  z-index: 99;
  position: -webkit-sticky; /* Safari */
  position: sticky;
  top: 0px;
  background-color: rgb(30, 30, 30);
}

.selected {
    border: 2px solid #ffd200;
}
.comment {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.v-slider__tick{
    background-color: rgba(190, 203, 245, 0.422);
}

.v-slider__tick--filled{
    background-color: #0277bd;
}

</style>
