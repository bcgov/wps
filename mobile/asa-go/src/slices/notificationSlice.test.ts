import { describe, expect, it } from 'vitest'
import notificationReducer, {
  dismissNotification,
  enqueueNotification,
  notificationInitialState,
  removeNotificationByKey
} from '@/slices/notificationSlice'
import { selectCurrentNotification } from '@/store'
import { createTestStore } from '@/testUtils'

describe('notificationSlice', () => {
  it('prioritizes transient severity and preserves FIFO order within a priority', () => {
    const store = createTestStore()
    store.dispatch(enqueueNotification({ message: 'first success', severity: 'success' }))
    store.dispatch(enqueueNotification({ message: 'second success', severity: 'success' }))
    store.dispatch(enqueueNotification({ message: 'warning', severity: 'warning' }))
    store.dispatch(enqueueNotification({ message: 'error', severity: 'error' }))

    expect(selectCurrentNotification(store.getState())?.message).toBe('error')
    store.dispatch(dismissNotification(selectCurrentNotification(store.getState())?.id ?? ''))
    expect(selectCurrentNotification(store.getState())?.message).toBe('warning')
    store.dispatch(dismissNotification(selectCurrentNotification(store.getState())?.id ?? ''))
    expect(selectCurrentNotification(store.getState())?.message).toBe('first success')
  })

  it('places persistent notifications behind every transient notification', () => {
    const store = createTestStore()
    store.dispatch(enqueueNotification({ autoHideDuration: null, message: 'persistent warning', severity: 'warning' }))
    store.dispatch(enqueueNotification({ message: 'success', severity: 'success' }))

    expect(selectCurrentNotification(store.getState())?.message).toBe('success')
    store.dispatch(dismissNotification(selectCurrentNotification(store.getState())?.id ?? ''))
    expect(selectCurrentNotification(store.getState())?.message).toBe('persistent warning')
  })

  it('updates an existing notification with the same deduplication key', () => {
    const firstState = notificationReducer(
      notificationInitialState,
      enqueueNotification({ dedupeKey: 'loading', message: 'data failed' })
    )
    const state = notificationReducer(
      firstState,
      enqueueNotification({ dedupeKey: 'loading', message: 'data and layers failed' })
    )

    expect(state.notifications).toHaveLength(1)
    expect(state.notifications[0].message).toBe('data and layers failed')
    expect(state.notifications[0].id).toBe(firstState.notifications[0].id)
  })

  it('dismisses by id and removes source-driven notifications by key', () => {
    const firstState = notificationReducer(
      notificationInitialState,
      enqueueNotification({ dedupeKey: 'registration', message: 'registration failed' })
    )
    const dismissedState = notificationReducer(firstState, dismissNotification(firstState.notifications[0].id))
    expect(dismissedState.notifications).toHaveLength(0)

    const restoredState = notificationReducer(
      dismissedState,
      enqueueNotification({ dedupeKey: 'registration', message: 'registration failed' })
    )
    expect(notificationReducer(restoredState, removeNotificationByKey('registration')).notifications).toHaveLength(0)
  })
})
