import React from 'react'
import { Provider } from 'react-redux'
import 'index.css'
import store from 'app/store'
import * as serviceWorker from 'serviceWorker'
import { createRoot } from 'react-dom/client'

import App from './app/App'

const render = () => {
  const container = document.getElementById('root')
  if (!container) return
  const root = createRoot(container)
  root.render(
    <Provider store={store}>
      <App />
    </Provider>
  )
}

render()

if (process.env.NODE_ENV === 'development' && module.hot) {
  // As with the root reducer, we can hot-reload the React component tree
  // whenever a component file changes by reusing the render function
  module.hot.accept('app/App', render)
}

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
