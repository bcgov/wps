import { FireLayer } from 'api/external/fbaVectorSourceAPI'
import { FireCenter } from 'api/fbaAPI'
import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { IDBPDatabase, openDB } from 'idb'
import { isEqual, isUndefined, uniq } from 'lodash'

const fireCenterUrl =
  'https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/'

/**
 * Requests and caches vector data for fire centers/zones
 */
export class VectorDataManager {
  private axiosInstance: AxiosInstance
  private static dataStoreName = 'fireVectors'
  private static fireCenterNameIdx = 'fireCenterNameIdx'
  private db!: IDBPDatabase

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: fireCenterUrl
    })
  }

  public async init(): Promise<void> {
    this.db = await openDB('FireData', 1, {
      upgrade(db) {
        const fireCenterStore = db.createObjectStore(VectorDataManager.dataStoreName, {
          // Primary key, unique by layer and extent
          keyPath: 'cacheKey'
        })
        // For looking up fire centers by name
        fireCenterStore.createIndex(VectorDataManager.fireCenterNameIdx, 'name')
      }
    })
  }
  public async getOrSet(
    layer: FireLayer,
    extent: number[]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): Promise<AxiosResponse<any> | undefined> {
    const cachedValue = await this.db.get(
      VectorDataManager.dataStoreName,
      this.buildKey(layer, extent)
    )
    if (!isUndefined(cachedValue)) {
      return cachedValue.data
    }

    try {
      const { data } = await this.axiosInstance.get(this.buildUrl(layer, extent))
      if (data.features.length > 0) {
        const records = this.buildRecord(
          layer,
          extent,
          this.buildKey(layer, extent),
          data
        )
        const tx = this.db.transaction(VectorDataManager.dataStoreName, 'readwrite')
        await Promise.all(records.map(record => tx.store.put(record)))
      }
      return data
    } catch (error) {
      console.log(error)
      return undefined
    }
  }

  public async getFireCenter(fireCenter: FireCenter): Promise<void> {
    const data = await this.db.getFromIndex(
      VectorDataManager.dataStoreName,
      VectorDataManager.fireCenterNameIdx,
      fireCenter.name
    )

    return data
  }

  public buildRecord(
    layer: FireLayer,
    extent: number[],
    cacheKey: string,
    data: { features: { attributes: { MOF_FIRE_CENTRE_NAME: string } }[] }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ): { name?: string; cacheKey: string; data: any }[] {
    if (isEqual(layer, '2')) {
      const fireCenterNames = uniq(
        data.features.map(feature => feature.attributes.MOF_FIRE_CENTRE_NAME)
      )

      // Fire Center record
      const records = fireCenterNames.map(fireCenterName => ({
        name: fireCenterName,
        cacheKey,
        extent,
        data
      }))
      return records
    } else {
      // Fire Zones, unstructured
      return [
        {
          cacheKey,
          data
        }
      ]
    }
  }

  public buildKey(layer: FireLayer, extent: number[]): string {
    return `${layer}${extent.join(',')}`
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
