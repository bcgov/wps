import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { authenticate, testAuthenticate } from 'features/auth/slices/authenticationSlice'
import axios from 'api/axios'
import { AppDispatch, AppThunk } from 'app/store'
import { selectToken, selectAuthentication } from 'app/rootReducer'
import { TEST_AUTH } from 'utils/env'

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
  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)

  useEffect(() => {
    if (TEST_AUTH || window.Cypress) {
      dispatch(testAuthenticate(true, 'test token', 'test id token'))
    } else {
      dispatch(authenticate())
      dispatch(setAxiosRequestInterceptors())
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return <div>{error}</div>
  }

  if (authenticating) {
    return <div>Signing in...</div>
  }

  if (!isAuthenticated) {
    return <div>You are not authenticated!</div>
  }

  return children
}

export default React.memo(AuthWrapper)
