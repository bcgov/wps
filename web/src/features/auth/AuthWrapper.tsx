import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectAuthentication } from 'app/rootReducer'
import {
  authenticate,
  setAxiosRequestInterceptors,
} from 'features/auth/slices/authenticationSlice'

interface Props {
  shouldAuthenticate: boolean
  children: React.ReactElement
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
