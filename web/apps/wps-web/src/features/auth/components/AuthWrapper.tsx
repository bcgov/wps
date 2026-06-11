import * as Sentry from '@sentry/browser'
import axios from '@wps/api/axios'
import { TEST_AUTH } from '@wps/utils/env'
import { selectAuthentication, selectToken } from 'app/rootReducer'
import type { AppDispatch, AppThunk } from 'app/store'
import { authenticate, testAuthenticate } from 'features/auth/slices/authenticationSlice'
import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

interface Props {
  children: React.ReactElement
}

const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use(config => {
    const token = selectToken(getState())
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  })
}

const AuthWrapper = ({ children }: Props) => {
  const dispatch: AppDispatch = useDispatch()
  const { isAuthenticated, authenticating, error, email } = useSelector(selectAuthentication)

  useEffect(() => {
    if (TEST_AUTH || window.Playwright) {
      dispatch(testAuthenticate(true, 'test token', 'test id token'))
    } else {
      dispatch(authenticate())
      dispatch(setAxiosRequestInterceptors())
    }
  }, [])

  if (error) {
    return <div>{error}</div>
  }

  if (authenticating) {
    return <div>Signing in...</div>
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>
  }

  Sentry.setUser({ email: email })

  return <React.StrictMode>{children}</React.StrictMode>
}

export default React.memo(AuthWrapper)
