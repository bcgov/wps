import { Fill, Style, Text, Stroke } from 'ol/style'

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
