import React from 'react'
import ReactDOM from 'react-dom'
import { Provider } from 'react-redux'

import 'index.css'
import store from 'app/store'
import * as serviceWorker from 'serviceWorker'

const render = () => {
  const App = require('app/App').default

  ReactDOM.render(
    <Provider store={store}>
      <App />
    </Provider>,
    document.getElementById('root')
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
