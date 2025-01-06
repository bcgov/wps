import { findLayerByName } from '@/features/riskMap/mapFunctions'
import { Fill, Style, Text, Stroke } from 'ol/style'
import CircleStyle from 'ol/style/Circle'
import { Map } from 'ol'

export const firePerimeterStyler = (feature: any) => {
  const labelText = feature.get('FIRE_NUMBER') || ''
  return new Style({
    fill: new Fill({
      color: 'rgba(251,171,96, 0.8)'
    }),
    text: new Text({
      font: '12px Calibri,sans-serif',
      text: labelText,
      fill: new Fill({
        color: '#000'
      }),
      stroke: new Stroke({
        color: '#fff',
        width: 2
      })
    })
  })
}

const highlightStyle = new Style({
  image: new CircleStyle({
    radius: 7,
    fill: new Fill({ color: 'rgba(255, 255, 255, 0.4)' }),
    stroke: new Stroke({ color: 'rgba(204, 85, 0, 0.9)', width: 2 })
  })
})

export const highlightFeature = (map: Map, layerName: string, id: string | number) => {
  const layer = findLayerByName(map, layerName)
  const feature = layer?.getSource()?.getFeatureById(id)

  if (feature) {
    feature.setStyle(highlightStyle)
  }
}

export const resetLayerStyle = (map: Map, layerName: string) => {
  const layer = findLayerByName(map, layerName)
  const source = layer?.getSource()

  if (source) {
    source.getFeatures().forEach(feat => {
      feat.setStyle(null)
    })
  }
}
