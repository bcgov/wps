import React from 'react'
import * as ReactDOMClient from 'react-dom/client'
import { Provider } from 'react-redux'
import App from 'app/App'

import 'index.css'
import store from 'app/store'
import * as serviceWorker from 'serviceWorker'

const render = () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const container = document.getElementById('root')
  // Null check to keep TypeScript happy
  if (container === null) {
    throw new Error('Root container is missing in index.html')
  }
  const root = ReactDOMClient.createRoot(container)
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
