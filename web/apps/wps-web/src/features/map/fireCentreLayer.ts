import type { FireCentre } from '@wps/types/fireCentre'
import { PMTILES_BUCKET } from '@wps/utils/env'
import VectorTileLayer from 'ol/layer/VectorTile'
import { PMTilesVectorSource } from 'ol-pmtiles'
import { fireCentreLineStyler, fireCentreStyler } from '@/features/map/fireCentreStylers'

export const FIRE_CENTRE_LAYER_NAME = 'fireCentreVector'
export const FIRE_CENTRE_LINE_LAYER_NAME = 'fireCentreLineVector'
const FIRE_CENTRES_PMTILES_FILENAME = 'fireCentres.pmtiles'
const DEFAULT_FIRE_CENTRE_Z_INDEX = 51
const DEFAULT_FIRE_CENTRE_LINE_Z_INDEX = 52

export interface FireCentrePMTilesLayerOptions {
  selectedFireCentre?: FireCentre
  source?: PMTilesVectorSource
  zIndex?: number
}

export const createPMTilesVectorSource = (filename: string) =>
  new PMTilesVectorSource({
    url: `${PMTILES_BUCKET}${filename}`
  })

export const createFireCentrePMTilesSource = () => createPMTilesVectorSource(FIRE_CENTRES_PMTILES_FILENAME)

export const getFireCentreHighlightPMTilesLayer = ({
  selectedFireCentre,
  source = createFireCentrePMTilesSource(),
  zIndex = DEFAULT_FIRE_CENTRE_Z_INDEX
}: FireCentrePMTilesLayerOptions = {}) =>
  new VectorTileLayer({
    source,
    style: fireCentreStyler(selectedFireCentre),
    zIndex,
    properties: { name: FIRE_CENTRE_LAYER_NAME }
  })

export const getFireCentreLinePMTilesLayer = ({
  selectedFireCentre,
  source = createFireCentrePMTilesSource(),
  zIndex = DEFAULT_FIRE_CENTRE_LINE_Z_INDEX
}: FireCentrePMTilesLayerOptions = {}) =>
  new VectorTileLayer({
    source,
    style: fireCentreLineStyler(selectedFireCentre),
    zIndex,
    properties: { name: FIRE_CENTRE_LINE_LAYER_NAME }
  })

export const getFireCentrePMTilesLayers = ({
  selectedFireCentre,
  zIndex = DEFAULT_FIRE_CENTRE_Z_INDEX
}: FireCentrePMTilesLayerOptions = {}) => {
  const source = createFireCentrePMTilesSource()
  const fireCentreLayer = getFireCentreHighlightPMTilesLayer({ selectedFireCentre, source, zIndex })
  const fireCentreLineLayer = getFireCentreLinePMTilesLayer({ selectedFireCentre, source, zIndex: zIndex + 1 })

  return { fireCentreLayer, fireCentreLineLayer }
}
