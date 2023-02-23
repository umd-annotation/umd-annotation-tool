<script lang="ts">
import {
  ref, Ref, watch, nextTick, defineComponent,
} from '@vue/composition-api';

export default defineComponent({
  name: 'Prompt',
  props: {},
  setup() {
    const show = ref(false);
    const title = ref('');
    const text: Ref<string | string[]> = ref('');
    const positiveButton = ref('Confirm');
    const negativeButton = ref('Cancel');
    const selected = ref('positive');
    const alert: Ref<undefined | 'warning' | 'error' | 'info'> = ref(undefined);
    const confirm = ref(false);

    /**
     * Placeholder resolver function.  Wrapped in object so that
     * its reference isn't changed on reassign.
     */
    const functions = {
      resolve(val: boolean) {
        return val;
      },
    };

    const positive: Ref<HTMLFormElement | null> = ref(null);
    const negative: Ref<HTMLFormElement | null> = ref(null);

    async function clickPositive() {
      show.value = false;
      functions.resolve(true);
    }

    async function clickNegative() {
      show.value = false;
      functions.resolve(false);
    }

    async function select() {
      if (selected.value === 'positive') {
        clickPositive();
      } else {
        clickNegative();
      }
    }

    async function focusPositive() {
      if (positive.value) {
        // vuetify 2 hack: need to add extra .$el property, may be removed in vuetify 3
        positive.value.$el.focus();
        selected.value = 'positive';
      }
    }

    async function focusNegative() {
      if (negative.value) {
        // vuetify 2 hack: need to add extra .$el property, may be removed in vuetify 3
        negative.value.$el.focus();
        selected.value = 'negative';
      }
    }

    watch(show, async (value) => {
      if (!value) {
        functions.resolve(false);
      } else if (positive.value) {
        selected.value = 'positive';
        // Needs to mount and then dialog transition, single tick doesn't work
        await nextTick();
        await nextTick();
        // vuetify 2 hack: need to add extra .$el property, may be removed in vuetify 3
        positive.value.$el.focus();
      }
    });

    return {
      alert,
      show,
      title,
      text,
      positiveButton,
      negativeButton,
      selected,
      confirm,
      functions,
      clickPositive,
      clickNegative,
      select,
      positive,
      negative,
      focusPositive,
      focusNegative,
    };
  },
});
</script>

<template>
  <v-dialog
    v-model="show"
    max-width="400"
  >
    <v-card>
      <v-card-title
        v-if="title"
        v-mousetrap="[
          { bind: 'left', handler: () => focusNegative(), disable: !show },
          { bind: 'right', handler: () => focusPositive(), disable: !show },
          { bind: 'enter', handler: () => select(), disable: !show },
        ]"
        style="width:100%"
        class="ma-0"
      >
        <v-alert
          v-if="alert"
          :type="alert"
          prominent
          width="400"
        >
          <div class="alertText">
            {{ title }}
          </div>
        </v-alert>
        <div
          v-else
          class="titletext"
        >
          {{ title }}
        </div>
      </v-card-title>
      <v-card-text
        v-if="Array.isArray(text)"
      >
        <div
          v-for="(item,key) in text"
          :key="key"
        >
          {{ item }}
        </div>
      </v-card-text>
      <v-card-text
        v-else
        class="text"
      >
        {{ text }}
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          v-if="confirm && negativeButton && negativeButton.length"
          ref="negative"
          text
          @click="clickNegative"
        >
          {{ negativeButton }}
        </v-btn>
        <v-btn
          ref="positive"
          color="primary"
          text
          @click="clickPositive"
        >
          {{ positiveButton }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<style scoped>
.titletext{
  font-size:2em !important;
}
.alertText {
  font-size: 1.5em !important;
  width:100%;
}
.text{
  font-size:1.5em;
}
</style>
