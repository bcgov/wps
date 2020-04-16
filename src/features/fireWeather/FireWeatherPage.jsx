import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { selectAuthenticationReducer } from 'app/rootReducer'
import {
  getAuthenticationSuccess,
  resetAuthentication,
  getAuthenticationFailed
} from 'features/auth/slices/authenticationSlice'

export const FireWeatherPage = () => {
  const { isAuthenticated } = useSelector(selectAuthenticationReducer)
  const dispatch = useDispatch()

  useEffect(() => {
    const keycloak = window.Keycloak({
      url: process.env.REACT_APP_KEYCLOAK_AUTH_URL,
      realm: process.env.REACT_APP_KEYCLOAK_REALM,
      clientId: process.env.REACT_APP_KEYCLOAK_CLIENT
    })
    keycloak
      .init({
        onLoad: 'login-required',
        promiseType: 'native',
        checkLoginIframe: false
      })
      .then(authenticated => {
        if (!authenticated) {
          dispatch(resetAuthentication())
          window.location.reload()
        } else {
          dispatch(getAuthenticationSuccess(authenticated))
        }
        setTimeout(() => {
          keycloak.updateToken(60)
        }, 6000)
      })
      .catch(err => {
        dispatch(getAuthenticationFailed(err))
      })
  }, [dispatch])

  if (!isAuthenticated) {
    return <div>Page is loading...</div>
  }

  return <div>This is fire weather page</div>
}
