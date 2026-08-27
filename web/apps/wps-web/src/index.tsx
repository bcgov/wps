import createCache from '@emotion/cache'
import { CacheProvider } from '@emotion/react'
import { API_BASE_URL, SENTRY_DSN, SENTRY_ENV } from '@wps/utils/env'
import App from 'app/App'
import * as ReactDOMClient from 'react-dom/client'
import { Provider } from 'react-redux'

import './index.css'
import * as Sentry from '@sentry/react'
import { feedbackIntegration } from '@sentry/react'
import { theme } from '@wps/ui/theme'
import store from 'app/store'

// Matches the style-src nonce nginx sets on the Content-Security-Policy header for this
// response (see the __CSP_NONCE__ substitution in index.html and openshift/nginx.conf),
// so Emotion's injected <style> tags satisfy CSP without needing 'unsafe-inline'.
const cspNonce = document.querySelector('meta[property="csp-nonce"]')?.getAttribute('content') ?? undefined
// prepend: true replicates <StyledEngineProvider injectFirst> (MUI styles load first, so
// app-level overrides win) - MUI's own CSP guide says to use this instead of
// StyledEngineProvider once a custom/nonce-carrying cache is in play, since
// StyledEngineProvider's injectFirst otherwise creates its own cache with no nonce.
const emotionCache = createCache({ key: 'css', nonce: cspNonce, prepend: true })

const render = () => {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENV,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
      feedbackIntegration({
        autoInject: false,
        colorScheme: 'light',
        enableScreenshot: true,
        themeLight: {
          submitBackground: theme.palette.primary.main,
          submitBorder: theme.palette.primary.main,
          submitForeground: theme.palette.primary.contrastText,
          accentBackground: theme.palette.secondary.main,
          accentForeground: theme.palette.secondary.contrastText
        }
      })
    ],
    // Performance Monitoring
    tracesSampleRate: 0.5, //  Capture 50% of the transactions
    // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
    tracePropagationTargets: [API_BASE_URL],
    // Session Replay
    replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0 // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  })
  const container = document.getElementById('root')
  // Null check to keep TypeScript happy
  if (container === null) {
    throw new Error('Root container is missing in index.html')
  }
  const root = ReactDOMClient.createRoot(container)
  root.render(
    <CacheProvider value={emotionCache}>
      <Provider store={store}>
        <App />
      </Provider>
    </CacheProvider>
  )
}

// cache bust any stale js chunks
globalThis.addEventListener('vite:preloadError', _event => {
  globalThis.location.reload()
})

render()
