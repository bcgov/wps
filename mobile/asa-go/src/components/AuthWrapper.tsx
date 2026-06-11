import React from 'react'
import { useSelector } from 'react-redux'
import LandscapeLandingPage from '@/components/LandscapeLandingPage'
import PortraitLandingPage from '@/components/PortraitLandingPage'
import { useIsPortrait } from '@/hooks/useIsPortrait'
import { useIsTablet } from '@/hooks/useIsTablet'
import { selectAuthentication, selectNetworkStatus } from '@/store'

interface Props {
  children: React.ReactElement
}

const AuthWrapper = ({ children }: Props) => {
  const { sessionMode } = useSelector(selectAuthentication)
  const { networkStatus } = useSelector(selectNetworkStatus)
  const isPortrait = useIsPortrait()
  const isTablet = useIsTablet()

  if (sessionMode === 'authenticated' || !networkStatus.connected) {
    return <React.StrictMode>{children}</React.StrictMode>
  }

  // A phone in portrait orientation and all tablets have enough vertical real estate to render all the
  // landing page elements as a stack. Phones in landscape orientation need things re-organized.
  return isPortrait || isTablet ? <PortraitLandingPage /> : <LandscapeLandingPage />
}

export default React.memo(AuthWrapper)
