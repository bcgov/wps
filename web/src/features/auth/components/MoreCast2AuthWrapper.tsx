import React, { useEffect } from 'react'
import { WF1_AUTH_URL } from 'utils/env'

interface Props {
  children: React.ReactElement
}

const MoreCast2AuthWrapper = ({ children }: Props) => {
  useEffect(() => {
    async function fetchData() {
      if (!window.location.href.includes('access_token')) {
        window.location.href = WF1_AUTH_URL
      }
      console.log('We in')
    }

    fetchData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return children
}

export default React.memo(MoreCast2AuthWrapper)
