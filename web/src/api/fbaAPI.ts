import axios from 'api/axios'
import EsriJSON from 'ol/format/EsriJSON'

export interface FireCenterStation {
  code: number
  name: string
  zone?: string
}

export interface FireCenter {
  id: number
  name: string
  stations: FireCenterStation[]
}

export interface FBAResponse {
  fire_centers: FireCenter[]
}

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = '/fba/fire-centers'

  const { data } = await axios.get(url, {})
  return data
}

export async function getFireCenterVectorSource(url: string, projection: any) {
  const esriJsonFormat = new EsriJSON()
  const { data } = await axios.get(url, { params: { dataType: 'jsonp' } })
  const features = esriJsonFormat.readFeatures(data, {
    featureProjection: projection
  })
  return features
}
