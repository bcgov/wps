import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { authenticate } from 'features/auth/slices/authenticationSlice'
import axios from 'api/axios'
import { AppThunk } from 'app/store'
import { selectToken, selectAuthentication } from 'app/rootReducer'

interface Props {
  shouldAuthenticate: boolean
  children: React.ReactElement
}

export const setAxiosRequestInterceptors = (): AppThunk => (_, getState) => {
  // Use axios interceptors to intercept any requests and add authorization headers.
  axios.interceptors.request.use(config => {
    const token = selectToken(getState())
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  })
}

const AuthWrapper = ({ children, shouldAuthenticate }: Props) => {
  const dispatch = useDispatch()
  const { isAuthenticated, authenticating, error } = useSelector(selectAuthentication)

  useEffect(() => {
    if (shouldAuthenticate) {
      dispatch(authenticate())
      dispatch(setAxiosRequestInterceptors())
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (!shouldAuthenticate) {
    return children
  }

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
