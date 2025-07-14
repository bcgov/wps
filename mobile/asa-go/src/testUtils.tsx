import { RootState } from "@/store";
import { configureStore } from "@reduxjs/toolkit";

import { rootReducer } from "@/rootReducer";

export const createTestStore = (initialState: Partial<RootState> = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initialState,
    },
  });
};
