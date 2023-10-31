import { jwtDecode } from 'jwt-decode'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from 'app/store'
import { TEST_AUTH, WF1_AUTH_URL } from 'utils/env'
import { wf1Authenticate, wf1AuthenticateError } from 'features/auth/slices/wf1AuthenticationSlice'
import { selectAuthentication, selectWf1Authentication } from 'app/rootReducer'
import { ROLES } from 'features/auth/roles'

interface Props {
  children: React.ReactElement
}

const MoreCast2AuthWrapper = ({ children }: Props) => {
  const dispatch: AppDispatch = useDispatch()

  const [renderChildren, setRenderChildren] = useState(false)
  const { roles } = useSelector(selectAuthentication)
  const { error } = useSelector(selectWf1Authentication)

  const isAuthenticatedForecaster = roles.includes(ROLES.MORECAST_2.WRITE_FORECAST)

  useEffect(() => {
    async function fetchData() {
      if (TEST_AUTH || window.Cypress) {
        dispatch(wf1Authenticate('test token'))
        setRenderChildren(true)
      }

      if (!isAuthenticatedForecaster) {
        setRenderChildren(true)
      }

      if (!window.location.href?.includes('access_token') && isAuthenticatedForecaster) {
        window.location.href = `${WF1_AUTH_URL}&redirect_uri=${window.location.href}`
      }

      if (window.location.href?.includes('access_token')) {
        const wf1Token = window.location.href.split('#access_token=')[1].split('&')[0]
        try {
          jwtDecode(wf1Token)
          dispatch(wf1Authenticate(wf1Token))
          setRenderChildren(true)
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

  return renderChildren ? children : null
}

export default React.memo(MoreCast2AuthWrapper)
