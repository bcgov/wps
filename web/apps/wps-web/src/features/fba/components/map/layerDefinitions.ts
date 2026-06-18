import type { FireShape, FireShapeStatusDetail, RunType } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import type { DetailedGeoJsonStation, GeoJsonStation } from '@wps/types/stationTypes'
import { PMTILES_BUCKET } from '@wps/utils/env'
import {
  fireCentreLabelStyler,
  fireCentreLineStyler,
  fireCentreStyler,
  fireShapeLabelStyler,
  fireShapeLineStyler,
  fireShapeStyler,
  hfiStyler,
  stationStyler
} from 'features/fba/components/map/featureStylers'
import { buildPMTilesURL } from 'features/fba/pmtilesBuilder'
import type { DateTime } from 'luxon'
import GeoJSON from 'ol/format/GeoJSON'
import VectorLayer from 'ol/layer/Vector'
import VectorTileLayer from 'ol/layer/VectorTile'
import VectorSource from 'ol/source/Vector'
import { PMTilesVectorSource } from 'ol-pmtiles'

export const hfiLayerName = 'hfiVector'
export const zoneStatusLayerName = 'fireShapeVector'

type FBAStations = GeoJsonStation[] | DetailedGeoJsonStation[]

export interface FBAVectorLayers {
  fireCentreVTL: VectorTileLayer
  fireCentreLineVTL: VectorTileLayer
  fireShapeVTL: VectorTileLayer
  fireShapeHighlightVTL: VectorTileLayer
  fireCentreLabelVTL: VectorTileLayer
  fireShapeLabelVTL: VectorTileLayer
  baseLayers: VectorTileLayer[]
}

const createPMTilesVectorSource = (filename: string) =>
  new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}${filename}`
  })

export const createFBAVectorLayers = (): FBAVectorLayers => {
  const fireCentreVectorSource = createPMTilesVectorSource('fireCentres.pmtiles')
  const fireShapeVectorSource = createPMTilesVectorSource('fireZoneUnits.pmtiles')
  const fireCentreLabelVectorSource = createPMTilesVectorSource('fireCentreLabels.pmtiles')
  const fireShapeLabelVectorSource = createPMTilesVectorSource('fireZoneUnitLabels.pmtiles')

  const fireCentreVTL = new VectorTileLayer({
    source: fireCentreVectorSource,
    style: fireCentreStyler(undefined),
    zIndex: 51
  })

  const fireCentreLineVTL = new VectorTileLayer({
    source: fireCentreVectorSource,
    style: fireCentreLineStyler(undefined),
    zIndex: 52
  })

  const fireShapeVTL = new VectorTileLayer({
    source: fireShapeVectorSource,
    style: fireShapeStyler([], true),
    zIndex: 50,
    properties: { name: zoneStatusLayerName }
  })

  const fireShapeHighlightVTL = new VectorTileLayer({
    source: fireShapeVectorSource,
    style: fireShapeLineStyler([], undefined),
    zIndex: 53,
    properties: { name: zoneStatusLayerName }
  })

  const fireCentreLabelVTL = new VectorTileLayer({
    source: fireCentreLabelVectorSource,
    style: fireCentreLabelStyler,
    zIndex: 100,
    maxZoom: 6
  })

  const fireShapeLabelVTL = new VectorTileLayer({
    declutter: true,
    source: fireShapeLabelVectorSource,
    style: fireShapeLabelStyler(undefined),
    zIndex: 99,
    minZoom: 6
  })

  return {
    fireCentreVTL,
    fireCentreLineVTL,
    fireShapeVTL,
    fireShapeHighlightVTL,
    fireCentreLabelVTL,
    fireShapeLabelVTL,
    baseLayers: [
      fireCentreVTL,
      fireCentreLineVTL,
      fireShapeVTL,
      fireShapeHighlightVTL,
      fireCentreLabelVTL,
      fireShapeLabelVTL
    ]
  }
}

export const createHFILayer = (forDate: DateTime, runType: RunType, runDate: DateTime, visible: boolean) => {
  return new VectorTileLayer({
    source: new PMTilesVectorSource({
      url: buildPMTilesURL(forDate, runType, runDate)
    }),
    style: hfiStyler,
    zIndex: 100,
    minZoom: 4,
    properties: { name: hfiLayerName },
    visible
  })
}

export const createStationsLayer = (stations: FBAStations) => {
  const stationsSource = new VectorSource({
    features: new GeoJSON().readFeatures(
      { type: 'FeatureCollection', features: stations },
      {
        featureProjection: 'EPSG:3857'
      }
    )
  })

  return new VectorLayer({
    source: stationsSource,
    minZoom: 6,
    style: stationStyler,
    zIndex: 51
  })
}

export const setFBASelectionStyles = (
  layers: FBAVectorLayers,
  selectedFireCentre: FireCentre | undefined,
  selectedFireShape: FireShape | undefined,
  provincialSummaryZones: FireShapeStatusDetail[],
  showShapeStatus: boolean
) => {
  layers.fireCentreVTL.setStyle(fireCentreStyler(selectedFireCentre))
  layers.fireShapeVTL.setStyle(fireShapeStyler(provincialSummaryZones, showShapeStatus))
  layers.fireShapeLabelVTL.setStyle(fireShapeLabelStyler(selectedFireShape))
  layers.fireShapeHighlightVTL.setStyle(fireShapeLineStyler(provincialSummaryZones, selectedFireShape))
  layers.fireCentreLineVTL.setStyle(fireCentreLineStyler(selectedFireCentre))

  layers.fireShapeVTL.changed()
  layers.fireShapeHighlightVTL.changed()
  layers.fireShapeLabelVTL.changed()
  layers.fireCentreLineVTL.changed()
  layers.fireCentreVTL.changed()
}
