import { configureStore, type ThunkAction, type UnknownAction } from '@reduxjs/toolkit'
import rootReducer, { type RootState } from 'app/rootReducer'

const store = configureStore({
  reducer: rootReducer,
  // Some redux state can be VERY big - which causes huge slowdowns in development.
  // immutableCheck and serializableCheck are disabled (see below) to avoid this.
  // TODO: see if a better solution can be found: https://reactjs.org/docs/hooks-reference.html#usereducer
  // import { configureStore, Action, getDefaultMiddleware } from '@reduxjs/toolkit'
  middleware: getDefaultMiddleware => getDefaultMiddleware({ immutableCheck: false, serializableCheck: false })
})

export type AppDispatch = typeof store.dispatch

export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, unknown, UnknownAction>

export default store
