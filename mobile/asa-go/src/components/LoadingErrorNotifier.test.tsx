import { ThemeProvider } from '@mui/material'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import LoadingErrorNotifier from '@/components/LoadingErrorNotifier'
import NotificationCenter from '@/components/NotificationCenter'
import { NOTIFICATION_DEFINITIONS } from '@/notificationDefinitions'
import { initialState as dataInitialState, getDataFailed, getDataStart } from '@/slices/dataSlice'
import { updateNetworkStatus } from '@/slices/networkStatusSlice'
import { getFireCentreInfoStart, initialState as settingsInitialState } from '@/slices/settingsSlice'
import { createTestStore } from '@/testUtils'
import { theme } from '@/theme'
import { createLoadError, type LoadError } from '@/utils/loadError'

const renderSnackbar = ({
  connected = true,
  dataError = null,
  settingsError = null
}: {
  connected?: boolean
  dataError?: LoadError | null
  settingsError?: LoadError | null
} = {}) => {
  const store = createTestStore({
    data: { ...dataInitialState, error: dataError },
    settings: { ...settingsInitialState, error: settingsError },
    networkStatus: {
      networkStatus: { connected, connectionType: connected ? 'wifi' : 'none' }
    }
  })

  const view = render(
    <ThemeProvider theme={theme}>
      <Provider store={store}>
        <div style={{ position: 'relative' }}>
          <LoadingErrorNotifier />
          <NotificationCenter />
        </div>
      </Provider>
    </ThemeProvider>
  )

  return { store, ...view }
}

describe('LoadingErrorNotifier', () => {
  it('shows one friendly operational data error', () => {
    renderSnackbar({ dataError: createLoadError('Error: API failed') })

    expect(screen.getByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).toBeInTheDocument()
    expect(screen.queryByText('Error: API failed')).not.toBeInTheDocument()
    expect(screen.getByTestId('CancelOutlinedIcon')).toHaveStyle({ color: '#E7000B' })
  })

  it('shows a settings data error globally', () => {
    renderSnackbar({ settingsError: createLoadError('Error: settings failed') })

    expect(screen.getByText(NOTIFICATION_DEFINITIONS.settingsDataError.message)).toBeInTheDocument()
  })

  it('prioritizes settings errors when both sources fail', () => {
    renderSnackbar({ dataError: createLoadError('API failed'), settingsError: createLoadError('Settings failed') })

    expect(screen.getByText(NOTIFICATION_DEFINITIONS.settingsDataError.message)).toBeInTheDocument()
    expect(screen.queryByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).not.toBeInTheDocument()
  })

  it('shows a remaining operational error after a settings error clears', () => {
    const { store } = renderSnackbar({
      dataError: createLoadError('API failed'),
      settingsError: createLoadError('Settings failed')
    })

    act(() => {
      store.dispatch(getFireCentreInfoStart())
    })

    expect(screen.getByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).toBeInTheDocument()
  })

  it('does not show an API error encountered offline after reconnecting', () => {
    const { store } = renderSnackbar({ connected: false, dataError: createLoadError('offline') })

    act(() => {
      store.dispatch(updateNetworkStatus({ connected: true, connectionType: 'wifi' }))
    })

    expect(screen.queryByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).not.toBeInTheDocument()
  })

  it('does not reopen a dismissed error until it clears and occurs again', async () => {
    const { store } = renderSnackbar({ dataError: createLoadError('API failed') })

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    await waitFor(() =>
      expect(screen.queryByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).not.toBeInTheDocument()
    )

    act(() => {
      store.dispatch(getDataStart())
    })
    act(() => {
      store.dispatch(getDataFailed(createLoadError('API failed')))
    })

    expect(screen.getByText(NOTIFICATION_DEFINITIONS.operationalDataError.message)).toBeInTheDocument()
  })

  it('prefixes an available status code', () => {
    renderSnackbar({ dataError: { key: 'API failed', status: 503 } })

    expect(screen.getByText(`503 Error - ${NOTIFICATION_DEFINITIONS.operationalDataError.message}`)).toBeInTheDocument()
  })
})
