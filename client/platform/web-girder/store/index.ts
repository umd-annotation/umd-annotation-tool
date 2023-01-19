import Vue from 'vue';
import Vuex from 'vuex';

import router from '../router';
import { RootState } from './types';
import Location from './Location';
import Dataset from './Dataset';
import Brand from './Brand';
import Groups from './Groups';
import Jobs, { init as JobsInit } from './Jobs';
import girderRest from '../plugins/girder';

Vue.use(Vuex);

const store = new Vuex.Store<RootState>({
  modules: {
    Brand,
    Location,
    Dataset,
    Jobs,
    Groups,
  },
});

/* Keep location state up to date with current route */
router.beforeEach((to, from, next) => {
  if (girderRest.user?.groups?.length && to.name !== 'viewer' && to.name !== 'annotatorPage') {
    const annotatorId = store.state.Groups.groupMap?.Annotator;
    if (girderRest.user.groups.includes(annotatorId)) {
      next('/annotatorPage');
      return;
    }
  } else if (to.name === 'home') {
    store.dispatch('Location/setLocationFromRoute', to);
  }
  next();
});

JobsInit(store);

export default store;
