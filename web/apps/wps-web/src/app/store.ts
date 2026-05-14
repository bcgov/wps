import { configureStore, ThunkAction, UnknownAction } from '@reduxjs/toolkit'
import rootReducer, { RootState } from 'app/rootReducer'

const store = configureStore({
  reducer: rootReducer,
  // c-haines data is VERY big - so causes huge slowdowns in development,
  // when doing c-haines development you may wish to disable immutableCheck
  // and serializableCheck (see below)
  // TODO: see if a better solution can be found: https://reactjs.org/docs/hooks-reference.html#usereducer
  // import { configureStore, Action, getDefaultMiddleware } from '@reduxjs/toolkit'
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware({ immutableCheck: false, serializableCheck: false })
})

export type AppDispatch = typeof store.dispatch

export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, unknown, UnknownAction>

export default store
