import { ThemeProvider } from '@mui/material'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import LoadingErrorNotifier from '@/components/LoadingErrorNotifier'
import NotificationCenter from '@/components/NotificationCenter'
import { initialState as dataInitialState, getDataFailed, getDataStart } from '@/slices/dataSlice'
import { updateNetworkStatus } from '@/slices/networkStatusSlice'
import { initialState as settingsInitialState } from '@/slices/settingsSlice'
import { createTestStore } from '@/testUtils'
import { theme } from '@/theme'
import { NavPanel } from '@/utils/constants'

const OPERATIONAL_DATA_ERROR_MESSAGE = 'Unable to update operational data. Displayed data may be stale.'
const SETTINGS_DATA_ERROR_MESSAGE = 'Unable to load notification settings. Check your connection and try again.'
const MAP_LAYER_ERROR_MESSAGE = 'Unable to load one or more map layers. Some map information may be unavailable.'
const MAP_DATA_AND_LAYER_ERROR_MESSAGE = 'Unable to update map data or layers. Some information may be unavailable.'

const renderSnackbar = ({
  activeTab = NavPanel.MAP,
  connected = true,
  dataError = null,
  settingsError = null,
  layerErrorVersion = 0
}: {
  activeTab?: NavPanel
  connected?: boolean
  dataError?: string | null
  settingsError?: string | null
  layerErrorVersion?: number
} = {}) => {
  const store = createTestStore({
    data: { ...dataInitialState, error: dataError },
    settings: { ...settingsInitialState, error: settingsError },
    mapLayers: { pendingLoads: 0, latestErrorVersion: layerErrorVersion },
    networkStatus: {
      networkStatus: { connected, connectionType: connected ? 'wifi' : 'none' }
    }
  })

  const view = render(
    <ThemeProvider theme={theme}>
      <Provider store={store}>
        <div style={{ position: 'relative' }}>
          <LoadingErrorNotifier activeTab={activeTab} />
          <NotificationCenter />
        </div>
      </Provider>
    </ThemeProvider>
  )

  return { store, ...view }
}

describe('LoadingErrorNotifier', () => {
  it('shows one friendly operational data error on data tabs', () => {
    renderSnackbar({ activeTab: NavPanel.PROFILE, dataError: 'Error: API failed' })

    expect(screen.getByText(OPERATIONAL_DATA_ERROR_MESSAGE)).toBeInTheDocument()
    expect(screen.queryByText('Error: API failed')).not.toBeInTheDocument()
    expect(screen.getByTestId('CancelOutlinedIcon')).toHaveStyle({ color: '#E7000B' })
  })

  it('shows the settings data error only on Settings', () => {
    const { rerender, store } = renderSnackbar({ settingsError: 'Error: settings failed' })

    expect(screen.queryByText(SETTINGS_DATA_ERROR_MESSAGE)).not.toBeInTheDocument()

    rerender(
      <ThemeProvider theme={theme}>
        <Provider store={store}>
          <div style={{ position: 'relative' }}>
            <LoadingErrorNotifier activeTab={NavPanel.SETTINGS} />
            <NotificationCenter />
          </div>
        </Provider>
      </ThemeProvider>
    )
    expect(screen.getByText(SETTINGS_DATA_ERROR_MESSAGE)).toBeInTheDocument()
  })

  it('suppresses API errors offline but still shows layer failures on Map', () => {
    renderSnackbar({ connected: false, dataError: 'offline', layerErrorVersion: 1 })

    expect(screen.getByText(MAP_LAYER_ERROR_MESSAGE)).toBeInTheDocument()
    expect(screen.queryByText(OPERATIONAL_DATA_ERROR_MESSAGE)).not.toBeInTheDocument()
  })

  it('aggregates operational and layer failures on Map', () => {
    renderSnackbar({ dataError: 'API failed', layerErrorVersion: 1 })

    expect(screen.getByText(MAP_DATA_AND_LAYER_ERROR_MESSAGE)).toBeInTheDocument()
    expect(screen.queryByText(OPERATIONAL_DATA_ERROR_MESSAGE)).not.toBeInTheDocument()
    expect(screen.queryByText(MAP_LAYER_ERROR_MESSAGE)).not.toBeInTheDocument()
  })

  it('does not show a Map layer failure on another tab', () => {
    renderSnackbar({ activeTab: NavPanel.ADVISORY, layerErrorVersion: 1 })

    expect(screen.queryByText(MAP_LAYER_ERROR_MESSAGE)).not.toBeInTheDocument()
  })

  it('defers a layer failure until the Map tab is opened', () => {
    const { rerender, store } = renderSnackbar({ activeTab: NavPanel.ADVISORY, layerErrorVersion: 1 })

    rerender(
      <ThemeProvider theme={theme}>
        <Provider store={store}>
          <div style={{ position: 'relative' }}>
            <LoadingErrorNotifier activeTab={NavPanel.MAP} />
            <NotificationCenter />
          </div>
        </Provider>
      </ThemeProvider>
    )

    expect(screen.getByText(MAP_LAYER_ERROR_MESSAGE)).toBeInTheDocument()
  })

  it('does not show an API error encountered offline after reconnecting', () => {
    const { store } = renderSnackbar({ connected: false, dataError: 'offline' })

    act(() => {
      store.dispatch(updateNetworkStatus({ connected: true, connectionType: 'wifi' }))
    })

    expect(screen.queryByText(OPERATIONAL_DATA_ERROR_MESSAGE)).not.toBeInTheDocument()
  })

  it('does not reopen a dismissed error until it clears and occurs again', async () => {
    const { store } = renderSnackbar({ dataError: 'API failed' })

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    await waitFor(() => expect(screen.queryByText(OPERATIONAL_DATA_ERROR_MESSAGE)).not.toBeInTheDocument())

    act(() => {
      store.dispatch(getDataStart())
    })
    act(() => {
      store.dispatch(getDataFailed('API failed'))
    })

    expect(screen.getByText(OPERATIONAL_DATA_ERROR_MESSAGE)).toBeInTheDocument()
  })
})
