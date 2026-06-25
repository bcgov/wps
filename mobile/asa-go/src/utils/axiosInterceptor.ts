import * as Sentry from '@sentry/capacitor'
import type { InternalAxiosRequestConfig } from 'axios'
import { isNil } from 'lodash'
import axios from '@/api/axios'
import {
  authenticateFinished,
  decodeUserDetails,
  resetAuthentication
} from '@/slices/authenticationSlice'
import { selectAuthentication, store } from '@/store'
import { API_BASE_URL, API_PUBLIC_BASE_URL } from '@/utils/env'
import { Keycloak } from '../../../keycloak/src'

let interceptorsConfigured = false

interface RetriableAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retryAfterAuthRefresh?: boolean
}

export const configureApiInterceptors = () => {
  if (interceptorsConfigured) {
    return
  }

  interceptorsConfigured = true

  axios.interceptors.request.use(config => {
    const { sessionMode, token } = selectAuthentication(store.getState())
    if (sessionMode === 'authenticated' && !isNil(token)) {
      config.baseURL = API_BASE_URL
      config.headers.set('Authorization', `Bearer ${token}`)
    } else {
      config.baseURL = `${API_PUBLIC_BASE_URL}/asa-go`
      config.headers.delete('Authorization')
    }

    return config
  })

  axios.interceptors.response.use(
    // If there is a response we simply return it
    response => response,

    // If there is a 401 error we try the offline token before forcing re-authentication.
    async error => {
      const originalRequest = error?.config as RetriableAxiosRequestConfig | undefined
      if (error?.response?.status === 401) {
        if (originalRequest && originalRequest._retryAfterAuthRefresh !== true) {
          originalRequest._retryAfterAuthRefresh = true
          const refreshResult = await Keycloak.refreshAuthState()
          if (refreshResult.isAuthenticated && refreshResult.accessToken) {
            store.dispatch(
              authenticateFinished({
                token: refreshResult.accessToken,
                idToken: refreshResult.idToken
              })
            )
            const userDetails = decodeUserDetails(refreshResult.accessToken)
            Sentry.setUser(userDetails ? { email: userDetails.email } : null)
            originalRequest.baseURL = API_BASE_URL
            originalRequest.headers.set('Authorization', `Bearer ${refreshResult.accessToken}`)
            return axios(originalRequest)
          }
        }

        try {
          await Keycloak.clearAuthState()
        } catch {
          // keep resetting app auth even if native storage cleanup fails
        }
        store.dispatch(resetAuthentication())
        Sentry.setUser(null)
      }
      return Promise.reject(error)
    }
  )
}
