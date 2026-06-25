import type { InternalAxiosRequestConfig } from 'axios'
import axios from '@/api/axios'
import { authenticateFinished, resetAuthentication, setSentryUserFromToken } from '@/slices/authenticationSlice'
import { selectAuthentication, store } from '@/store'
import { API_BASE_URL, API_PUBLIC_BASE_URL } from '@/utils/env'
import { Keycloak } from '../../../keycloak/src'

let interceptorsConfigured = false

interface RetriableAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retryAfterAuthRefresh?: boolean
}

const configureRequestBaseUrl = (config: InternalAxiosRequestConfig) => {
  const { sessionMode, token } = selectAuthentication(store.getState())
  if (sessionMode === 'authenticated' && token != null) {
    config.baseURL = API_BASE_URL
    config.headers.set('Authorization', `Bearer ${token}`)
    return config
  }

  config.baseURL = `${API_PUBLIC_BASE_URL}/asa-go`
  config.headers.delete('Authorization')
  return config
}

const retryWithRefreshedToken = async (request: RetriableAxiosRequestConfig | undefined) => {
  if (!request || request._retryAfterAuthRefresh === true) {
    return
  }

  request._retryAfterAuthRefresh = true
  const refreshResult = await Keycloak.refreshAuthState()
  if (!refreshResult.isAuthenticated || !refreshResult.accessToken) {
    return
  }

  store.dispatch(
    authenticateFinished({
      token: refreshResult.accessToken,
      idToken: refreshResult.idToken
    })
  )
  setSentryUserFromToken(refreshResult.accessToken)
  request.baseURL = API_BASE_URL
  request.headers.set('Authorization', `Bearer ${refreshResult.accessToken}`)
  return axios(request)
}

const resetStoredAuthentication = async () => {
  try {
    await Keycloak.clearAuthState()
  } catch {
    // keep resetting app auth even if native storage cleanup fails
  }
  store.dispatch(resetAuthentication())
  setSentryUserFromToken(undefined)
}

export const configureApiInterceptors = () => {
  if (interceptorsConfigured) {
    return
  }

  interceptorsConfigured = true

  axios.interceptors.request.use(configureRequestBaseUrl)

  axios.interceptors.response.use(
    // If there is a response we simply return it
    response => response,

    // If there is a 401 error we try the offline token before forcing re-authentication.
    async error => {
      if (error?.response?.status !== 401) {
        throw error
      }

      const retryResponse = await retryWithRefreshedToken(error?.config as RetriableAxiosRequestConfig | undefined)
      if (retryResponse) {
        return retryResponse
      }

      await resetStoredAuthentication()
      throw error
    }
  )
}
