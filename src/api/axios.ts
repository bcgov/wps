import axios from 'axios'

// TODO: Replace baseURL with '{{.Env.API_BASE_URL}}' when using Caddy
const instance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL
})

export default instance
