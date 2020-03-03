import axios from 'axios'

const local = 'http://localhost:8080'
const isBuilt = process.env.NODE_ENV === 'production'
// const baseURL = isBuilt ? '{{.Env.API_BASE_URL}}' : local
const baseURL = isBuilt ? process.env.REACT_APP_API_BASE_URL : local

const instance = axios.create({
  baseURL: baseURL
})

export default instance
