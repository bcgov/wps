import { COORDINATE_TOLERANCE } from '@/features/smurfi/components/map/spotMapFeatureUtils'
import { createSpotStatusIcon } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { SelectedCoordinates } from '@/features/smurfi/interfaces'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { FeatureLike } from 'ol/Feature'
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style'

const createHighlightStyle = () =>
  new Style({
    image: new CircleStyle({
      radius: 20,
      fill: new Fill({ color: 'rgba(255, 255, 0, 0.3)' }),
      stroke: new Stroke({ color: '#FFD700', width: 3 })
    })
  })

export const createSpotMarkerStyle = (selectedCoords: SelectedCoordinates | null | undefined) => {
  return (feature: FeatureLike) => {
    const status = feature.get('status') as SpotRequestStatus
    const featureLon = feature.get('lon') as number
    const featureLat = feature.get('lat') as number

    const baseStyle = new Style({
      image: createSpotStatusIcon(status)
    })

    if (
      selectedCoords &&
      Math.abs(featureLon - selectedCoords.longitude) < COORDINATE_TOLERANCE &&
      Math.abs(featureLat - selectedCoords.latitude) < COORDINATE_TOLERANCE
    ) {
      return [createHighlightStyle(), baseStyle]
    }

    return baseStyle
  }
}

export const createForecastMarkerStyle = (feature: FeatureLike) => {
  const status = feature.get('status') as SpotRequestStatus
  return new Style({
    image: createSpotStatusIcon(status, 0.65, 0.65)
  })
}

export const forecastLineStyle = new Style({
  stroke: new Stroke({
    color: 'rgba(5, 54, 98, 0.35)',
    width: 2,
    lineDash: [6, 6]
  })
})
