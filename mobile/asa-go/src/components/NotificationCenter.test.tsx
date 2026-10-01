import { ThemeProvider } from '@mui/material'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { describe, expect, it } from 'vitest'
import NotificationCenter from '@/components/NotificationCenter'
import { dismissNotification, enqueueNotification } from '@/slices/notificationSlice'
import { initialState as pushNotificationInitialState, setRegistrationError } from '@/slices/pushNotificationSlice'
import { createTestStore } from '@/testUtils'
import { theme } from '@/theme'

const renderCenter = (store = createTestStore()) =>
  render(
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <div style={{ position: 'relative' }}>
          <NotificationCenter />
        </div>
      </ThemeProvider>
    </Provider>
  )

describe('NotificationCenter', () => {
  it('preempts and then resumes a persistent notification', async () => {
    const store = createTestStore()
    store.dispatch(
      enqueueNotification({
        autoHideDuration: null,
        dedupeKey: 'persistent',
        message: 'Persistent',
        severity: 'warning'
      })
    )
    const view = renderCenter(store)
    expect(screen.getByText('Persistent')).toBeInTheDocument()

    act(() => {
      store.dispatch(enqueueNotification({ message: 'Error', severity: 'error' }))
    })
    expect(screen.getByText('Error')).toBeInTheDocument()

    act(() => {
      store.dispatch(dismissNotification(store.getState().notifications.notifications[1].id))
    })
    expect(screen.getByText('Persistent')).toBeInTheDocument()
    view.unmount()
  })

  it('uses the standardized red circled X for errors', () => {
    const store = createTestStore()
    store.dispatch(enqueueNotification({ message: 'Error', severity: 'error' }))
    renderCenter(store)

    expect(screen.getByTestId('CancelOutlinedIcon')).toHaveStyle({ color: '#E7000B' })
  })

  it('ignores click-away closure but allows the close button', async () => {
    const store = createTestStore()
    store.dispatch(enqueueNotification({ message: 'Error' }))
    renderCenter(store)

    fireEvent.mouseDown(document.body)
    fireEvent.mouseUp(document.body)
    fireEvent.click(document.body)
    expect(screen.getByText('Error')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    await waitFor(() => expect(screen.queryByText('Error')).not.toBeInTheDocument())
  })

  it('keeps a dismissed registration warning hidden until the failure recurs', async () => {
    const store = createTestStore({
      networkStatus: { networkStatus: { connected: true, connectionType: 'wifi' } },
      pushNotification: {
        ...pushNotificationInitialState,
        pushNotificationPermission: 'granted',
        registrationError: true
      }
    })
    renderCenter(store)

    expect(
      await screen.findByText('Unable to register this device for notifications. Retrying automatically.')
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    await waitFor(() =>
      expect(
        screen.queryByText('Unable to register this device for notifications. Retrying automatically.')
      ).not.toBeInTheDocument()
    )

    act(() => {
      store.dispatch(setRegistrationError(false))
    })
    act(() => {
      store.dispatch(setRegistrationError(true))
    })

    expect(
      await screen.findByText('Unable to register this device for notifications. Retrying automatically.')
    ).toBeInTheDocument()
  })
})
