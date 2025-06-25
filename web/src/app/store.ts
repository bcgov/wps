import { configureStore, AnyAction, ThunkAction, UnknownAction } from '@reduxjs/toolkit'
import { thunk, ThunkMiddleware } from 'redux-thunk'
import rootReducer, { RootState } from 'app/rootReducer'

const thunkMiddleware: ThunkMiddleware<RootState, AnyAction> = thunk
const store = configureStore({
  reducer: rootReducer,
  // c-haines data is VERY big - so causes huge slowdowns in development,
  // when doing c-haines development you may wish to disable immutableCheck
  // and serializableCheck (see below)
  // TODO: see if a better solution can be found: https://reactjs.org/docs/hooks-reference.html#usereducer
  // import { configureStore, Action, getDefaultMiddleware } from '@reduxjs/toolkit'
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware({ immutableCheck: false, serializableCheck: false }).concat(thunkMiddleware)
})

export type AppDispatch = typeof store.dispatch

export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, unknown, UnknownAction>

export default store
