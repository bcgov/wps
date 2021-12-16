import React from 'react'
import ReactDOM from 'react-dom'
import { Provider } from 'react-redux'

import store from './src/app/store'
import * as serviceWorker from './src/serviceWorker'
import App from './src/app/App'

const render = () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  ReactDOM.render(
    <Provider store={store}>
      <App />
    </Provider>,
    document.getElementById('root')
  )
}

render()

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()
