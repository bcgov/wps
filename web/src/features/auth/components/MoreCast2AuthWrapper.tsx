import * as jwtDecode from 'jwt-decode'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from 'app/store'
import { WF1_AUTH_URL } from 'utils/env'
import { wf1Authenticate, wf1AuthenticateError } from 'features/auth/slices/wf1AuthenticationSlice'
import { selectWf1Authentication } from 'app/rootReducer'

interface Props {
  children: React.ReactElement
}

const MoreCast2AuthWrapper = ({ children }: Props) => {
  const dispatch: AppDispatch = useDispatch()

  const { error } = useSelector(selectWf1Authentication)

  useEffect(() => {
    async function fetchData() {
      if (!window.location.href.includes('access_token')) {
        window.location.href = WF1_AUTH_URL
      } else {
        const wf1Token = window.location.href.split('#access_token=')[1].split('&')[0]
        try {
          jwtDecode.default(wf1Token)
          dispatch(wf1Authenticate(wf1Token))
        } catch (e) {
          dispatch(wf1AuthenticateError('Failed to authenticate with WF1'))
        }
      }
    }

    fetchData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return <div>{error}</div>
  }

  return children
}

export default React.memo(MoreCast2AuthWrapper)
