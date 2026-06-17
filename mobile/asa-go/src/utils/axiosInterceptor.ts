import * as Sentry from '@sentry/capacitor'
import { isNil } from 'lodash'
import axios from '@/api/axios'
import { resetAuthentication } from '@/slices/authenticationSlice'
import { selectAuthentication, store } from '@/store'
import { API_BASE_URL, API_PUBLIC_BASE_URL } from '@/utils/env'

let interceptorsConfigured = false

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

    // If there is a 401 error we force re-authentication; otherwise we forward the error.
    error => {
      if (error?.response?.status === 401) {
        store.dispatch(resetAuthentication())
        Sentry.setUser(null)
      }
      return Promise.reject(error)
    }
  )
}
