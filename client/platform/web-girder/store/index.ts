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
  if (girderRest.user && !girderRest.user.admin && girderRest.user?.groups?.length && to.name !== 'viewer' && to.name !== 'annotatorHome') {
    const annotatorId = store.state.Groups.groupMap?.Annotator;
    const managerId = store.state.Groups.groupMap?.Manager;
    if (girderRest.user.groups.includes(annotatorId)
      && !girderRest.user.groups.includes(managerId)) {
      next('/annotatorHome');
      return;
    }
  } else if (to.name === 'home') {
    store.dispatch('Location/setLocationFromRoute', to);
  }
  next();
});

JobsInit(store);

export default store;
