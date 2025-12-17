import React from 'react'
import * as ReactDOMClient from 'react-dom/client'
import { Provider } from 'react-redux'
import App from 'app/App'
import { SENTRY_DSN, SENTRY_ENV, API_BASE_URL } from 'utils/env'
import { registerSW } from 'virtual:pwa-register'

import './index.css'
import store from 'app/store'
import * as Sentry from '@sentry/react'

const AppWrapper = () => {
  return (
    <Provider store={store}>
      <App />
    </Provider>
  )
}

const render = () => {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENV,
    integrations: [Sentry.browserTracingIntegration(), Sentry.replayIntegration()],
    // Performance Monitoring
    tracesSampleRate: 0.5, //  Capture 100% of the transactions
    // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: [API_BASE_URL],
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0 // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  })

  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const container = document.getElementById('root')
  // Null check to keep TypeScript happy
  if (container === null) {
    throw new Error('Root container is missing in index.html')
  }
  const root = ReactDOMClient.createRoot(container)
  root.render(<AppWrapper />)
}

// Register service worker to handle chunk loading and caching
registerSW({
  immediate: true,
  onOfflineReady() {
    console.log('App ready to work offline')
  },
  onRegisterError(error) {
    console.error('Service worker registration error:', error)
  }
})

render()
