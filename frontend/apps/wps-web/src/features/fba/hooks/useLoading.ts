import { selectCombinedASALoading } from '@/app/rootReducer'
import { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'

const LOADING_OVERLAY_DELAY_MS = 300

export const useLoading = (): boolean => {
  const loading = useSelector(selectCombinedASALoading)
  const [showLoading, setShowLoading] = useState<boolean>(false)

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout> | undefined
    if (loading) {
      setShowLoading(true)
    } else {
      timeout = setTimeout(() => setShowLoading(false), LOADING_OVERLAY_DELAY_MS)
    }
    return () => {
      if (timeout) clearTimeout(timeout)
    }
  }, [loading])

  return showLoading
}
