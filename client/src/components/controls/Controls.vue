<script lang="ts">
import {
  defineComponent, reactive, ref, watch,
} from '@vue/composition-api';
import { usePrompt } from 'dive-common/vue-utilities/prompt-service';
import context from 'dive-common/store/context';
import { injectAggregateController } from '../annotators/useMediaController';

export default defineComponent({
  name: 'Control',
  props: {
    maxSegment: {
      type: Number,
      default: -1,
    },
  },
  setup(props) {
    const data = reactive({
      frame: 0,
      dragging: false,
    });
    const mediaController = injectAggregateController().value;
    const { visible } = usePrompt();
    watch(mediaController.frame, (frame) => {
      if (!data.dragging) {
        data.frame = frame;
      }
    });
    const sliderKey = ref(false);
    const sliderDisabled = ref(false);
    const dragHandler = {
      start() { data.dragging = true; },
      end() {
        if (props.maxSegment !== -1 && sliderDisabled.value) {
          data.dragging = false;
          sliderDisabled.value = false;
          data.frame = (150 + (props.maxSegment + 2) * 450);
          sliderKey.value = !sliderKey.value;
        }
      },
    };
    function input(value: number) {
      if (mediaController.frame.value !== value) {
        if (props.maxSegment !== -1 && value > (150 + (props.maxSegment + 2) * 450)) {
          // eslint-disable-next-line no-param-reassign
          value = (150 + (props.maxSegment + 2) * 450);
          sliderDisabled.value = true;
        }
        mediaController.seek(value);
      }
      data.frame = value;
    }
    function togglePlay(_: HTMLElement, keyEvent: KeyboardEvent) {
      // Prevent scroll from spacebar and other default effects.
      keyEvent.preventDefault();
      if (mediaController.playing.value) {
        mediaController.pause();
      } else {
        mediaController.play();
      }
    }
    function toggleEnhancements() {
      context.toggle('ImageEnhancements');
    }

    const seekSegment = (direction: -1 | 1) => {
      const segment = Math.floor((mediaController.frame.value - 150) / 450);
      const frameMax = ((segment + 1) * 450) + 150;
      const frameMin = (segment * 450) + 150;
      if (direction > 0) {
        mediaController.seek(frameMax - 1);
      } else {
        mediaController.seek(frameMin);
      }
    };

    return {
      data,
      mediaController,
      dragHandler,
      input,
      togglePlay,
      toggleEnhancements,
      visible,
      sliderKey,
      sliderDisabled,
      seekSegment,
    };
  },
});
</script>

<template>
  <div
    v-mousetrap="[
      { bind: 'left', handler: mediaController.prevFrame, disabled: visible() },
      { bind: 'right', handler: mediaController.nextFrame, disabled: visible() },
      { bind: 'space', handler: togglePlay, disabled: visible() },
      { bind: 'f', handler: mediaController.nextFrame, disabled: visible() },
      { bind: 'd', handler: mediaController.prevFrame, disabled: visible() },
      {
        bind: 'l',
        handler: () => mediaController.toggleSynchronizeCameras(!mediaController.cameraSync.value),
        disabled: visible(),
      },
    ]"
  >
    <v-card
      class="px-4 py-1"
      tile
    >
      <v-slider
        :key="sliderKey"
        hide-details
        :min="0"
        :max="mediaController.maxFrame.value"
        :value="data.frame"
        :disabled="sliderDisabled"
        @start="dragHandler.start"
        @end="dragHandler.end"
        @change="dragHandler.end"
        @input="input($event)"
      />
      <v-row no-gutters>
        <v-col class="pl-1 py-1 shrink">
          <slot
            justify="start"
            name="timelineControls"
          />
        </v-col>
        <v-col
          class="py-1 shrink"
          style="min-width: 100px;"
        >
          <v-btn
            icon
            small
            title="seek to beginning of the current segment"
            @click="seekSegment(-1)"
          >
            <v-icon>mdi-skip-previous</v-icon>
          </v-btn>
          <v-btn
            v-if="!mediaController.playing.value"
            icon
            small
            title="(space) Play"
            @click="mediaController.play"
          >
            <v-icon>mdi-play</v-icon>
          </v-btn>
          <v-btn
            v-else
            icon
            small
            title="(space) Pause"
            @click="mediaController.pause"
          >
            <v-icon>mdi-pause</v-icon>
          </v-btn>
          <v-btn
            icon
            small
            title="seek to the end of the next segment"
            @click="seekSegment(1)"
          >
            <v-icon>mdi-skip-next</v-icon>
          </v-btn>
        </v-col>
        <v-col
          class="pl-1 py-1"
        >
          <slot name="middle" />
        </v-col>
        <v-col
          v-if="false"
          class="pl-1 py-1 shrink d-flex"
          align="right"
        >
          <v-btn
            icon
            small
            :color="mediaController.lockedCamera.value ? 'primary': 'default'"
            title="center camera on selected track"
            @click="mediaController.toggleLockedCamera"
          >
            <v-icon>
              {{ mediaController.lockedCamera.value ? 'mdi-lock-check' : 'mdi-lock-open' }}
            </v-icon>
          </v-btn>
          <v-btn
            icon
            small
            title="(r)eset pan and zoom"
            @click="mediaController.resetZoom"
          >
            <v-icon>mdi-image-filter-center-focus</v-icon>
          </v-btn>
          <v-btn
            icon
            small
            title="Image Enhancements"
            @click="toggleEnhancements"
          >
            <v-icon>mdi-contrast-box</v-icon>
          </v-btn>

          <v-btn
            v-if="mediaController.cameras.value.length > 1"
            icon
            small
            :color="mediaController.cameraSync.value ? 'primary': 'default'"
            title="Synchronize camera controls"

            @click="mediaController.toggleSynchronizeCameras(!mediaController.cameraSync.value)"
          >
            <v-icon>
              {{ mediaController.cameraSync.value ? 'mdi-link' : 'mdi-link-off' }}
            </v-icon>
          </v-btn>
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>
