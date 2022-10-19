import axios from 'axios'
import { API_BASE_URL, RASTER_SERVER_BASE_URL } from 'utils/env'

const instance = axios.create({
  baseURL: API_BASE_URL
})

export const raster = axios.create({
  baseURL: RASTER_SERVER_BASE_URL
})

export default instance
