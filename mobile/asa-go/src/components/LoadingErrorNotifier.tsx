import { useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { enqueueNotification, removeNotificationByKey } from '@/slices/notificationSlice'
import {
  type AppDispatch,
  type RootState,
  selectMapLayersLoadState,
  selectOperationalLoadState,
  selectSettingsLoadState
} from '@/store'
import { NavPanel } from '@/utils/constants'

const OPERATIONAL_DATA_ERROR_MESSAGE = 'Unable to update operational data. Displayed data may be stale.'
const SETTINGS_DATA_ERROR_MESSAGE = 'Unable to load notification settings. Check your connection and try again.'
const MAP_LAYER_ERROR_MESSAGE = 'Unable to load one or more map layers. Some map information may be unavailable.'
const MAP_DATA_AND_LAYER_ERROR_MESSAGE = 'Unable to update map data or layers. Some information may be unavailable.'

const LOADING_ERROR_NOTIFICATION_KEY = 'loading-error'

interface LoadingErrorNotifierProps {
  activeTab: NavPanel
}

const LoadingErrorNotifier = ({ activeTab }: LoadingErrorNotifierProps) => {
  const dispatch: AppDispatch = useDispatch()
  const connected = useSelector((state: RootState) => state.networkStatus.networkStatus.connected)
  const { errorKey: operationalError } = useSelector(selectOperationalLoadState)
  const { errorKey: settingsError } = useSelector(selectSettingsLoadState)
  const { errorKey: layerError } = useSelector(selectMapLayersLoadState)
  const seenOperationalError = useRef<string | null>(null)
  const seenSettingsError = useRef<string | null>(null)
  const seenLayerError = useRef<string | null>(null)

  useEffect(() => {
    if (!operationalError) seenOperationalError.current = null
    if (!settingsError) seenSettingsError.current = null

    // keep the persistent offline banner as the only network error shown while disconnected
    if (!connected) {
      seenOperationalError.current = operationalError
      seenSettingsError.current = settingsError
    }

    const operationalErrorPending =
      connected && operationalError !== null && operationalError !== seenOperationalError.current
    const settingsErrorPending = connected && settingsError !== null && settingsError !== seenSettingsError.current
    const layerErrorPending = layerError !== null && layerError !== seenLayerError.current

    let message = ''
    if (activeTab === NavPanel.SETTINGS) {
      if (settingsErrorPending) {
        message = SETTINGS_DATA_ERROR_MESSAGE
        seenSettingsError.current = settingsError
      }
    } else {
      const showOperationalError = operationalErrorPending
      const showLayerError = activeTab === NavPanel.MAP && layerErrorPending

      if (showOperationalError && showLayerError) {
        message = MAP_DATA_AND_LAYER_ERROR_MESSAGE
      } else if (showLayerError) {
        message = MAP_LAYER_ERROR_MESSAGE
      } else if (showOperationalError) {
        message = OPERATIONAL_DATA_ERROR_MESSAGE
      }

      if (showOperationalError) seenOperationalError.current = operationalError
      if (showLayerError) seenLayerError.current = layerError
    }

    if (message) {
      dispatch(
        enqueueNotification({
          dedupeKey: LOADING_ERROR_NOTIFICATION_KEY,
          message,
          severity: 'error'
        })
      )
    } else {
      dispatch(removeNotificationByKey(LOADING_ERROR_NOTIFICATION_KEY))
    }
  }, [activeTab, connected, dispatch, layerError, operationalError, settingsError])

  return null
}

export default LoadingErrorNotifier
