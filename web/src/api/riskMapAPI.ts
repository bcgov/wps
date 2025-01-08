import axios from 'api/axios'
import { Geometry } from 'ol/geom'
import { Feature } from 'ol'

export interface RiskOutput {
  id: number
  name: string
  distance: number
  bearing: number
  direction: string
}

export interface RiskOutputResponse {
  risk_outputs: RiskOutput[]
}

export interface FireShapeFeatures {
  features: Feature<Geometry>[]
}

export async function computeRisk(values: FireShapeFeatures, hotspots: FireShapeFeatures): Promise<RiskOutputResponse> {
  const url = 'risk-map/compute'
  const { data } = await axios.post(url, {
    values: {
      features: values.features
    },
    hotspots: {
      features: hotspots.features
    }
  })
  return data
}
