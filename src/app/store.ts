import { configureStore } from '@reduxjs/toolkit'

import rootReducer from 'app/rootReducer'

const store = configureStore({
  reducer: rootReducer
})

if (process.env.NODE_ENV === 'development' && module.hot) {
  // By using the module.hot API for reloading, we can re-import
  // the new version of the root reducer function whenever it's been recompiled,
  // and tell the store to use the new version instead.
  module.hot.accept('app/rootReducer', () => {
    const newRootReducer = require('app/rootReducer').default
    store.replaceReducer(newRootReducer)
  })
}

export type AppDispatch = typeof store.dispatch

export default store
