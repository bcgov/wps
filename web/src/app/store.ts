import { configureStore, Action } from '@reduxjs/toolkit'
import { ThunkAction } from 'redux-thunk'

import rootReducer, { RootState } from 'app/rootReducer'

const store = configureStore({
  reducer: rootReducer,
  // c-haines data is VERY big - so causes huge slowdowns in development,
  // when doing c-haines development you may wish to disable immutableCheck
  // and serializableCheck (see below)
  // TODO: see if a better solution can be found: https://reactjs.org/docs/hooks-reference.html#usereducer
  // import { configureStore, Action, getDefaultMiddleware } from '@reduxjs/toolkit'
  // middleware: () =>
  //   getDefaultMiddleware({
  //     immutableCheck: false,
  //     serializableCheck: false
  //   })
})

if (process.env.NODE_ENV === 'development' && module.hot) {
  // By using the module.hot API for reloading, we can re-import
  // the new version of the root reducer function whenever it's been recompiled,
  // and tell the store to use the new version instead.
  module.hot.accept('app/rootReducer', () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const newRootReducer = require('app/rootReducer').default
    store.replaceReducer(newRootReducer)
  })
}

export type AppDispatch = typeof store.dispatch

export type AppThunk = ThunkAction<void, RootState, null, Action<string>>

export default store
