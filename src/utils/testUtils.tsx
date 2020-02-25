import React from 'react'
import { render } from '@testing-library/react'
import { Provider } from 'react-redux'

import store from 'app/store'

export const renderWithRedux = (ui: React.ReactNode) => {
  return {
    ...render(<Provider store={store}>{ui}</Provider>),
    // Adding `store` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    store
  }
}
