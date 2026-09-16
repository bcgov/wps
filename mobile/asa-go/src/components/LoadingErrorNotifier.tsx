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

interface LoadingErrorKeys {
  operational: string | null
  settings: string | null
  layer: string | null
}

interface LoadingErrorFlags {
  operational: boolean
  settings: boolean
  layer: boolean
}

const getLoadingErrorMessage = ({ operational, settings, layer }: LoadingErrorFlags): string | null => {
  if (settings) return SETTINGS_DATA_ERROR_MESSAGE
  if (operational && layer) return MAP_DATA_AND_LAYER_ERROR_MESSAGE
  if (layer) return MAP_LAYER_ERROR_MESSAGE
  if (operational) return OPERATIONAL_DATA_ERROR_MESSAGE
  return null
}

// reset resolved errors, advance handled occurrences, and preserve errors deferred to another tab
const getHandledErrorKey = (errorKey: string | null, handledErrorKey: string | null, shouldMarkHandled: boolean) =>
  errorKey === null || shouldMarkHandled ? errorKey : handledErrorKey

const LoadingErrorNotifier = ({ activeTab }: LoadingErrorNotifierProps) => {
  const dispatch: AppDispatch = useDispatch()
  const connected = useSelector((state: RootState) => state.networkStatus.networkStatus.connected)
  const { errorKey: operationalError } = useSelector(selectOperationalLoadState)
  const { errorKey: settingsError } = useSelector(selectSettingsLoadState)
  const { errorKey: layerError } = useSelector(selectMapLayersLoadState)
  // source errors outlive dismissed notifications, so remember which occurrences were already handled
  const handledErrorKeys = useRef<LoadingErrorKeys>({ operational: null, settings: null, layer: null })

  useEffect(() => {
    const errorKeys: LoadingErrorKeys = {
      operational: operationalError,
      settings: settingsError,
      layer: layerError
    }
    const pendingErrors: LoadingErrorFlags = {
      operational:
        connected && errorKeys.operational !== null && errorKeys.operational !== handledErrorKeys.current.operational,
      settings: connected && errorKeys.settings !== null && errorKeys.settings !== handledErrorKeys.current.settings,
      layer: errorKeys.layer !== null && errorKeys.layer !== handledErrorKeys.current.layer
    }
    const visibleErrors: LoadingErrorFlags = {
      operational: activeTab !== NavPanel.SETTINGS && pendingErrors.operational,
      settings: activeTab === NavPanel.SETTINGS && pendingErrors.settings,
      layer: activeTab === NavPanel.MAP && pendingErrors.layer
    }
    const message = getLoadingErrorMessage(visibleErrors)

    handledErrorKeys.current = {
      // offline API failures are handled by the persistent InfoBar instead of a notification
      operational: getHandledErrorKey(
        errorKeys.operational,
        handledErrorKeys.current.operational,
        visibleErrors.operational || !connected
      ),
      settings: getHandledErrorKey(
        errorKeys.settings,
        handledErrorKeys.current.settings,
        visibleErrors.settings || !connected
      ),
      // layer failures remain pending until the Map tab can display them
      layer: getHandledErrorKey(errorKeys.layer, handledErrorKeys.current.layer, visibleErrors.layer)
    }

    const notificationAction = message
      ? enqueueNotification({
          dedupeKey: LOADING_ERROR_NOTIFICATION_KEY,
          message,
          severity: 'error'
        })
      : removeNotificationByKey(LOADING_ERROR_NOTIFICATION_KEY)

    dispatch(notificationAction)
  }, [activeTab, connected, dispatch, layerError, operationalError, settingsError])

  return null
}

export default LoadingErrorNotifier
