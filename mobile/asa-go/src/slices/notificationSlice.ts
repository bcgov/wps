import { createSlice, nanoid, type PayloadAction } from '@reduxjs/toolkit'

export type NotificationSeverity = 'error' | 'warning' | 'info' | 'success'

export interface AppNotification {
  autoHideDuration: number | null
  dedupeKey?: string
  id: string
  message: string
  severity: NotificationSeverity
}

export interface EnqueueNotificationPayload {
  autoHideDuration?: number | null
  dedupeKey?: string
  message: string
  severity?: NotificationSeverity
}

export interface NotificationState {
  notifications: AppNotification[]
}

export const notificationInitialState: NotificationState = {
  notifications: []
}

const notificationSlice = createSlice({
  name: 'notifications',
  initialState: notificationInitialState,
  reducers: {
    enqueueNotification: {
      reducer(state, action: PayloadAction<AppNotification>) {
        const existingNotification = action.payload.dedupeKey
          ? state.notifications.find(notification => notification.dedupeKey === action.payload.dedupeKey)
          : undefined

        if (existingNotification) {
          existingNotification.autoHideDuration = action.payload.autoHideDuration
          existingNotification.message = action.payload.message
          existingNotification.severity = action.payload.severity
          return
        }

        state.notifications.push(action.payload)
      },
      prepare(payload: EnqueueNotificationPayload) {
        return {
          payload: {
            autoHideDuration: payload.autoHideDuration === undefined ? 6000 : payload.autoHideDuration,
            dedupeKey: payload.dedupeKey,
            id: nanoid(),
            message: payload.message,
            severity: payload.severity ?? 'error'
          }
        }
      }
    },
    dismissNotification(state, action: PayloadAction<string>) {
      const index = state.notifications.findIndex(notification => notification.id === action.payload)
      if (index >= 0) state.notifications.splice(index, 1)
    },
    removeNotificationByKey(state, action: PayloadAction<string>) {
      const index = state.notifications.findIndex(notification => notification.dedupeKey === action.payload)
      if (index >= 0) state.notifications.splice(index, 1)
    }
  }
})

export const { dismissNotification, enqueueNotification, removeNotificationByKey } = notificationSlice.actions

const severityPriority: Record<NotificationSeverity, number> = {
  error: 4,
  warning: 3,
  info: 2,
  success: 1
}

export const getNotificationPriority = (notification: AppNotification) =>
  (notification.autoHideDuration === null ? 0 : 10) + severityPriority[notification.severity]

export default notificationSlice.reducer
