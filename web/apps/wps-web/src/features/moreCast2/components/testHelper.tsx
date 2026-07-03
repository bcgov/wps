import { combineReducers, configureStore } from '@reduxjs/toolkit'
import morecastInputValidSlice, { type ValidInputState } from '@/features/moreCast2/slices/validInputSlice'

export const buildTestStore = (initialState: ValidInputState) => {
  const rootReducer = combineReducers({
    morecastInputValid: morecastInputValidSlice
  })
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      morecastInputValid: initialState
    }
  })
  return testStore
}
