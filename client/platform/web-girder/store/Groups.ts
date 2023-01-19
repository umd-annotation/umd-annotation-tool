import { merge } from 'lodash';
import { Module } from 'vuex';

import { getGroupIds } from 'platform/web-girder/api';

import type { GroupState, RootState } from './types';


const groupModule: Module<GroupState, RootState> = {
  namespaced: true,
  state: {
    groupMap: {},
  },
  mutations: {
    setGroupState(state, data: GroupState) {
      state.groupMap = merge(state.groupMap, data);
    },
  },
  actions: {
    async loadGroups({ commit }) {
      commit('setGroupState', (await getGroupIds()));
    },
  },
};

export default groupModule;
