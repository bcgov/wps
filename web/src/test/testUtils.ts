import rootReducer, { RootState } from '@/app/rootReducer'
import { configureStore } from '@reduxjs/toolkit'

export const createTestStore = (initialState: Partial<RootState> = {}) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      ...initialState
    }
  })
}
