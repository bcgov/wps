import GeoJSON from 'ol/format/GeoJSON'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style'
import {
  CURRENT_FIRE_STATUS_OPTIONS,
  CurrentFireStatus,
  getVisibleCurrentFireStatusDefaults
} from '@/features/smurfi/components/map/mapLayerVisibility'

export interface CurrentFirePolygonAttributes {
  fireNumber: string | null
  fireSizeHectares: number | string | null
  fireStatus: string | null
  fireYear: number | string | null
}

const CURRENT_FIRE_POLYS_WFS_URL =
  'https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP/ows'
const CURRENT_FIRE_POLYS_TYPE_NAME = 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_POLYS_SP'

const CURRENT_FIRE_POINTS_WFS_URL =
  'https://openmaps.gov.bc.ca/geo/pub/WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_PNTS_SP/ows'
const CURRENT_FIRE_POINTS_TYPE_NAME = 'pub:WHSE_LAND_AND_NATURAL_RESOURCE.PROT_CURRENT_FIRE_PNTS_SP'

const ACTIVE_FIRE_FILTER = "FIRE_STATUS <> 'Out'"
const FIRE_LABEL_MAX_RESOLUTION = 1000

export const CURRENT_FIRE_STATUS_COLORS: Record<CurrentFireStatus, string> = {
  'Out of Control': '#D32F2F',
  'Being Held': '#F9A825',
  'Under Control': '#2E7D32'
}

interface CurrentFireLayerOptions {
  getVisibleStatuses?: () => readonly string[]
}

const currentFirePolygonsUrl = new URL(CURRENT_FIRE_POLYS_WFS_URL)
currentFirePolygonsUrl.search = new URLSearchParams({
  service: 'WFS',
  version: '2.0.0',
  request: 'GetFeature',
  typeNames: CURRENT_FIRE_POLYS_TYPE_NAME,
  outputFormat: 'application/json',
  srsName: 'EPSG:4326',
  CQL_FILTER: ACTIVE_FIRE_FILTER
}).toString()

const currentFirePointsUrl = new URL(CURRENT_FIRE_POINTS_WFS_URL)
currentFirePointsUrl.search = new URLSearchParams({
  service: 'WFS',
  version: '2.0.0',
  request: 'GetFeature',
  typeNames: CURRENT_FIRE_POINTS_TYPE_NAME,
  outputFormat: 'application/json',
  srsName: 'EPSG:4326',
  CQL_FILTER: ACTIVE_FIRE_FILTER
}).toString()

const buildCurrentFirePolygonsUrl = (cqlFilter: string) => {
  const url = new URL(CURRENT_FIRE_POLYS_WFS_URL)
  url.search = new URLSearchParams({
    service: 'WFS',
    version: '2.0.0',
    request: 'GetFeature',
    typeNames: CURRENT_FIRE_POLYS_TYPE_NAME,
    outputFormat: 'application/json',
    srsName: 'EPSG:4326',
    CQL_FILTER: cqlFilter
  }).toString()
  return url.toString()
}

export const fetchCurrentFireSizeByFireNumber = async (fireNumber: string): Promise<number | null> => {
  const escapedFireNumber = fireNumber.replaceAll("'", "''")
  const response = await fetch(
    buildCurrentFirePolygonsUrl(`${ACTIVE_FIRE_FILTER} AND FIRE_NUMBER = '${escapedFireNumber}'`)
  )
  const data = await response.json()
  const fireSize = data?.features?.[0]?.properties?.FIRE_SIZE_HECTARES
  const numericFireSize = Number(fireSize)
  return Number.isFinite(numericFireSize) ? numericFireSize : null
}

export const fetchCurrentFireSizesByFireNumbers = async (fireNumbers: string[]): Promise<(number | null)[]> =>
  Promise.all(fireNumbers.map(fetchCurrentFireSizeByFireNumber))

const createFireLabel = (feature: { get: (property: string) => string | undefined }, resolution: number) => {
  if (resolution > FIRE_LABEL_MAX_RESOLUTION) {
    return undefined
  }

  return new Text({
    text: feature.get('FIRE_NUMBER') ?? '',
    font: '600 12px sans-serif',
    overflow: true,
    fill: new Fill({
      color: '#2F1B16'
    }),
    stroke: new Stroke({
      color: '#FFFFFF',
      width: 3
    })
  })
}

const createPointFireLabel = (feature: { get: (property: string) => string | undefined }, resolution: number) => {
  const label = createFireLabel(feature, resolution)
  label?.setOffsetY(-12)
  return label
}

const currentFirePolygonStyle = (feature: { get: (property: string) => string | undefined }, resolution: number) =>
  new Style({
    stroke: new Stroke({
      color: '#B3261E',
      width: 2
    }),
    fill: new Fill({
      color: 'rgba(179, 38, 30, 0.16)'
    }),
    text: createFireLabel(feature, resolution)
  })

const isCurrentFireStatus = (status: string | undefined): status is CurrentFireStatus =>
  CURRENT_FIRE_STATUS_OPTIONS.includes(status as CurrentFireStatus)

const getCurrentFireStatusColor = (status: string | undefined) =>
  isCurrentFireStatus(status) ? CURRENT_FIRE_STATUS_COLORS[status] : '#757575'

const isFireStatusVisible = (
  feature: { get: (property: string) => string | undefined },
  visibleStatuses: readonly string[]
) => visibleStatuses.includes(feature.get('FIRE_STATUS') ?? '')

const currentFirePointStyle = (feature: { get: (property: string) => string | undefined }, resolution: number) =>
  new Style({
    image: new CircleStyle({
      radius: 5,
      fill: new Fill({
        color: getCurrentFireStatusColor(feature.get('FIRE_STATUS'))
      }),
      stroke: new Stroke({
        color: '#FFFFFF',
        width: 1.5
      })
    }),
    text: createPointFireLabel(feature, resolution)
  })

const createCurrentFirePolygonStyle =
  ({ getVisibleStatuses = getVisibleCurrentFireStatusDefaults }: CurrentFireLayerOptions) =>
  (feature: { get: (property: string) => string | undefined }, resolution: number) =>
    isFireStatusVisible(feature, getVisibleStatuses()) ? currentFirePolygonStyle(feature, resolution) : undefined

const createCurrentFirePointStyle =
  ({ getVisibleStatuses = getVisibleCurrentFireStatusDefaults }: CurrentFireLayerOptions) =>
  (feature: { get: (property: string) => string | undefined }, resolution: number) =>
    isFireStatusVisible(feature, getVisibleStatuses()) ? currentFirePointStyle(feature, resolution) : undefined

export const getCurrentFirePolygonAttributes = (feature: {
  get: (property: string) => string | number | null | undefined
}): CurrentFirePolygonAttributes => ({
  fireNumber: feature.get('FIRE_NUMBER')?.toString() ?? null,
  fireSizeHectares: feature.get('FIRE_SIZE_HECTARES') ?? null,
  fireStatus: feature.get('FIRE_STATUS')?.toString() ?? null,
  fireYear: feature.get('FIRE_YEAR') ?? null
})

export const getCurrentFirePointAttributes = (feature: {
  get: (property: string) => string | number | null | undefined
}): CurrentFirePolygonAttributes => ({
  fireNumber: feature.get('FIRE_NUMBER')?.toString() ?? null,
  fireSizeHectares: feature.get('CURRENT_SIZE') ?? null,
  fireStatus: feature.get('FIRE_STATUS')?.toString() ?? null,
  fireYear: feature.get('FIRE_YEAR') ?? null
})

export const createCurrentFirePolygonsLayer = (options: CurrentFireLayerOptions = {}) =>
  new VectorLayer({
    source: new VectorSource({
      format: new GeoJSON(),
      url: currentFirePolygonsUrl.toString()
    }),
    style: createCurrentFirePolygonStyle(options),
    zIndex: 20
  })

export const createCurrentFirePointsLayer = (options: CurrentFireLayerOptions = {}) =>
  new VectorLayer({
    source: new VectorSource({
      format: new GeoJSON(),
      url: currentFirePointsUrl.toString()
    }),
    style: createCurrentFirePointStyle(options),
    zIndex: 30
  })
