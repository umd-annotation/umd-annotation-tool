import Vue from 'vue';
import Vuetify from 'vuetify/lib';
import colors from 'vuetify/lib/util/colors';
import { merge } from 'lodash';

import '@mdi/font/css/materialdesignicons.css';
import { ThemeOptions } from 'vuetify/types/services/theme';
import { vuetifyConfig } from '@girder/components/src';

Vue.use(Vuetify);

function getVuetify(config: unknown) {
  const theme: ThemeOptions & { customVariables: string[]} = {
    dark: true,
    customVariables: ['~/assets/variables.scss'],
    options: {
      customProperties: true,
    },
    themes: {
      dark: {
        accent: '#ffd200',
        primary: '#e21833',
        accentBackground: '#2c7596',
        baseText: '#ffd200',
      },
    },
  };
  const appVuetifyConfig = merge(vuetifyConfig, config, { theme });
  return new Vuetify(appVuetifyConfig);
}

export default getVuetify;
