import { Device } from '@capacitor/device'
import { useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'
import { setDeviceIdError } from '@/slices/pushNotificationSlice'
import type { AppDispatch } from '@/store'

export function useDeviceId(): string | null {
  const dispatch = useDispatch<AppDispatch>()
  const [deviceId, setDeviceId] = useState<string | null>(null)

  useEffect(() => {
    Device.getId()
      .then(({ identifier }) => {
        dispatch(setDeviceIdError(false))
        setDeviceId(identifier)
      })
      .catch(e => {
        console.error(`Failed to get device ID: ${e}`)
        dispatch(setDeviceIdError(true))
      })
  }, [dispatch])

  return deviceId
}
