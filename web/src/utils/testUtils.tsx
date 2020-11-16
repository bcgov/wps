import React from 'react'
import { configureStore } from '@reduxjs/toolkit'
import { render } from '@testing-library/react'
import { Provider } from 'react-redux'

import rootReducer from 'app/rootReducer'

const createStore = () => {
  return configureStore({
    reducer: rootReducer
  })
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export const renderWithRedux = (ui: React.ReactNode) => {
  const store = createStore()

  return {
    ...render(<Provider store={store}>{ui}</Provider>),
    // Adding `store` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    store
  }
}
