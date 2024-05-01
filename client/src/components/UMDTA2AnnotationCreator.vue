<script lang="ts">
import {
  computed, defineComponent, watch, onMounted, ref, Ref,
} from '@vue/composition-api';

import TooltipBtn from 'vue-media-annotator/components/TooltipButton.vue';
import StackedVirtualSidebarContainer from 'dive-common/components/StackedVirtualSidebarContainer.vue';
import {
  useCameraStore,
  useHandler,
  useSelectedTrackId,
  useTime,
} from 'vue-media-annotator/provides';
import { clientSettings } from 'dive-common/store/settings';
import { cloneDeep } from 'lodash';
import { AnnotationId } from 'vue-media-annotator/BaseAnnotation';


export default defineComponent({
  name: 'UMDTA2Annotation',

  components: {
    StackedVirtualSidebarContainer,
    TooltipBtn,
  },

  props: {
    width: {
      type: Number,
      default: 500,
    },
  },

  setup() {
    const selectedTrackIdRef = useSelectedTrackId();
    const speakerList = ref(['FLE', 'SME']);

    const { frame, maxSegment } = useTime();
    const handler = useHandler();
    const cameraStore = useCameraStore();


    const speaker: Ref<'FLE' | 'SME' | null> = ref(null);

    const firstTrack = cameraStore.getAnyPossibleTrack(0);

    const firstSpeaker = () => {
      if (firstTrack && firstTrack.attributes) {
        speaker.value = firstTrack.attributes.speaker as 'FLE' | 'SME' | null;
      }
    };
    firstSpeaker();

    clientSettings.trackSettings.newTrackSettings.modeSettings.Track.interpolate = true;
    if (firstTrack) {
      handler.trackSelect(0, false);
      handler.seekToFrame(firstTrack.begin);
    }

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


    const initialize = async () => {
      handler.setMaxSegment(99999);
    };
    onMounted(() => initialize());


    const hasPrevious = computed(() => {
      if (selectedTrackIdRef.value !== null && selectedTrackIdRef.value > 0) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value - 1);
        if (newTrack) {
          return newTrack.id;
        }
        return false;
      }
      return false;
    });

    const hasNext = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const newTrack = cameraStore.getAnyPossibleTrack(selectedTrackIdRef.value + 1);
        if (newTrack) {
          return newTrack.id;
        }
        return false;
      }
      return false;
    });

    const changeTrack = (direction: -1 | 1) => {
      handler.trackSelectNext(direction, true);
    };

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

    const trackFrames = computed(() => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (track) {
          return { begin: track.begin, end: track.end };
        }
      }
      return null;
    });

    watch(selectedTrackIdRef, () => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        if (track) {
          if (track.attributes && track.attributes.speaker) {
            speaker.value = track.attributes.speaker as 'FLE' | 'SME';
          } else {
            speaker.value = null;
          }
        }
      }
    });

    const updateSpeaker = (data: 'FLE' | 'SME' | null) => {
      if (selectedTrackIdRef.value !== null) {
        const track = cameraStore.getAnyTrack(selectedTrackIdRef.value);
        track.setAttribute('speaker', data);
        speaker.value = data;
        handler.save();
      }
    };
    const reOrderTracks = (newTrackId: AnnotationId) => {
      const tracks = cameraStore.sortedTracks;
      const trackCopy = cloneDeep(tracks.value);
      trackCopy.sort((a, b) => a.begin - b.begin);
      let updatedTrackId = -1;
      // Now we have a sorted list by the begin point instead of the trackId.
      // So we need to update the tracks so they have the proper begin/end times
      const trackIds = cameraStore.sortedTracks.value.map((item) => item.id);
      handler.trackSelect(null, false);
      handler.removeTrack(trackIds, true);
      trackCopy.forEach((item, index) => {
        // eslint-disable-next-line no-param-reassign
        item.id = index;
        if (item.id !== index && item.id === newTrackId) {
          updatedTrackId = index;
        }
        handler.addReplacementTrack(item);
      });
      if (newTrackId !== -1) {
        handler.trackSelect(newTrackId, false);
      }
      return updatedTrackId;
    };

    const createTurn = () => {
      const trackId = handler.addFullFrameTrack('turn', 100);
      if (trackId !== null) {
        handler.trackSelect(trackId, false);
        const updatedTrackId = reOrderTracks(trackId);
        if (updatedTrackId === -1) {
          handler.trackSelectNext(1);
        } else {
          handler.trackSelect(updatedTrackId, false);
        }
        handler.save();
      }
    };
    const deleteTurn = () => {
      if (selectedTrackIdRef.value !== null) {
        handler.removeTrack([selectedTrackIdRef.value], true);
        reOrderTracks(selectedTrackIdRef.value);
        handler.trackSelectNext(-1);
        handler.save();
      }
    };
    const setFrame = (pos: 'begin' | 'end') => {
      if (selectedTrackIdRef.value !== null) {
        const baseId = selectedTrackIdRef.value;
        handler.updateFullFrame(selectedTrackIdRef.value, pos);
        reOrderTracks(selectedTrackIdRef.value);
        if (baseId) {
          handler.trackSelect(baseId, false);
        }
        handler.save();
      }
    };

    return {
      hasPrevious,
      hasNext,
      selectedTrackIdRef,
      frame,
      trackFrames,
      outsideSegment,
      speaker,
      speakerList,
      changeTrack,
      seekBegin,
      seekEnd,
      playSegment,
      createTurn,
      deleteTurn,
      setFrame,
      updateSpeaker,
    };
  },
});
</script>


<template>
  <v-container class="maincontainer">
    <div>
      <v-row
        v-if="selectedTrackIdRef !== null"
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
          :disabled="hasPrevious === false"
          class="mx-2"
          @click="changeTrack(-1)"
        >
          Prev
        </v-btn>
        <v-btn
          color="primary"
          :disabled="hasNext === false"
          class="mx-2"
          @click="changeTrack(1)"
        >
          Next
        </v-btn>
      </v-row>
      <v-row>
        <v-btn
          color="primary"
          class="mx-2"
          @click="createTurn()"
        >
          Create Turn
        </v-btn>
        <v-btn
          v-if="selectedTrackIdRef !== null"
          color="primary"
          class="mx-2"
          @click="deleteTurn()"
        >
          Delete Turn
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </v-row>
      <v-row v-if="trackFrames">
        <v-col><div><span>Begin Frame:</span><span>{{ trackFrames.begin }}</span></div></v-col>
        <v-col><div><span>End Frame:</span><span>{{ trackFrames.end }}</span></div></v-col>
      </v-row>
      <v-row v-if="selectedTrackIdRef !== null && trackFrames">
        <v-col>
          <v-btn
            color="primary"
            class="mx-2"
            :disabled="frame > trackFrames.end"
            @click="setFrame('begin')"
          >
            Set Begin Frame
          </v-btn>
        </v-col>
        <v-col>
          <v-btn
            color="primary"
            class="mx-2"
            :disabled="frame < trackFrames.begin"
            @click="setFrame('end')"
          >
            Set End Frame
          </v-btn>
        </v-col>
      </v-row>
      <v-row
        v-if="selectedTrackIdRef !== null"
        class="py-1"
      >
        <v-select
          :value="speaker"
          class="pl-8"
          width="200px"
          label="Speaker"
          :items="speakerList"
          @change="updateSpeaker($event)"
        />
        <v-spacer />
      </v-row>
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
