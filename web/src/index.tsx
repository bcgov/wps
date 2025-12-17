import React, { useState, useEffect } from 'react'
import * as ReactDOMClient from 'react-dom/client'
import { Provider } from 'react-redux'
import App from 'app/App'
import { SENTRY_DSN, SENTRY_ENV, API_BASE_URL } from 'utils/env'
import { registerSW } from 'virtual:pwa-register'
import { Snackbar, Button } from '@mui/material'

import './index.css'
import store from 'app/store'
import * as Sentry from '@sentry/react'

// Global state for update notification
let triggerUpdateUI: (() => void) | null = null
let updateCallback: ((reloadPage?: boolean) => Promise<void>) | null = null

const UpdateNotification = () => {
  const [showUpdate, setShowUpdate] = useState(false)

  useEffect(() => {
    triggerUpdateUI = () => setShowUpdate(true)
    return () => {
      triggerUpdateUI = null
    }
  }, [])

  const handleUpdate = () => {
    setShowUpdate(false)
    if (updateCallback) {
      updateCallback(true)
    }
  }

  return (
    <Snackbar
      open={showUpdate}
      message="New version available!"
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      action={
        <Button color="primary" size="small" onClick={handleUpdate}>
          Ok
        </Button>
      }
    />
  )
}

const AppWrapper = () => {
  return (
    <Provider store={store}>
      <App />
      <UpdateNotification />
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
updateCallback = registerSW({
  immediate: true,
  onNeedRefresh() {
    // Show update notification when new version is available
    if (triggerUpdateUI) {
      triggerUpdateUI()
    }
  },
  onOfflineReady() {
    console.log('App ready to work offline')
  },
  onRegisterError(error) {
    console.error('Service worker registration error:', error)
  }
})

render()
