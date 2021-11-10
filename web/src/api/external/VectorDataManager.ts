import { FireLayer } from 'api/external/fbaVectorSourceAPI'
import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { get, set } from 'idb-keyval'
import { isUndefined } from 'lodash'

const fireCenterUrl =
  'https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/'

/**
 * Requests and caches vector data for fire centers/zones
 */
export class VectorDataManager {
  private axiosInstance: AxiosInstance
  constructor() {
    this.axiosInstance = axios.create({
      baseURL: fireCenterUrl
    })
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  public async getOrSet(layer: FireLayer, extent: number[]): Promise<AxiosResponse<any>> {
    const cachedValue = await get(this.buildKey(layer, extent))
    if (!isUndefined(cachedValue)) {
      return cachedValue
    }

    const { data } = await this.axiosInstance.get(this.buildUrl(layer, extent))
    set(this.buildKey(layer, extent), data)
    return data
  }

  public buildKey(layer: FireLayer, extent: number[]): string {
    return `${layer}-${extent.join(',')}`
  }

  public buildUrl(layer: FireLayer, extent: number[]): string {
    const url =
      layer +
      '/query/?f=json&' +
      'returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=' +
      // Extent, see description here:
      // https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
      encodeURIComponent(
        '{"xmin":' +
          extent[0] +
          ',"ymin":' +
          extent[1] +
          ',"xmax":' +
          extent[2] +
          ',"ymax":' +
          extent[3] +
          ',"spatialReference":{"wkid":102100}}'
      ) +
      // Quantization Parameter, see description here:
      // https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
      encodeURIComponent(
        `
      {
        "mode": "view", "originPosition": "upperLeft", "tolerance": ${1222.992452562501},
        "extent":
          { "type":"extent",
            "xmin":${extent[0]},
            "ymin":${extent[1]},
            "xmax":${extent[2]},
            "ymax":${extent[3]},
            "spatialReference":{"wkid":102100}}
      }
      `
      ) +
      '&geometryType=esriGeometryEnvelope&inSR=102100&outFields=*' +
      '&outSR=102100'
    return url
  }
}
