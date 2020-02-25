import axios from 'axios'

const isBundled = process.env.NODE_ENV === 'production'

// Temporary prod base url
const prod = 'https://wps-api-dev-6-secure-auzhsi.pathfinder.gov.bc.ca'
const local = 'http://localhost:8080'

// Todo: Replace this when Environment variable is ready to be used
// const baseURL = isBundled ? '{{.Env.API_BASE_URL}}' : local
const baseURL = isBundled ? prod : local

const instance = axios.create({ baseURL })

export default instance
