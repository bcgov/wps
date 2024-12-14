import Papa from 'papaparse'

export const hotSpotCSVToGeoJSON = (csvText: string) => {
  const parsed = Papa.parse(csvText, {
    header: true,
    skipEmptyLines: true
  })

  const features = parsed.data
    .map((row: any) => {
      const lon = parseFloat(row.longitude)
      const lat = parseFloat(row.latitude)

      if (isNaN(lon) || isNaN(lat)) return null

      return {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [lon, lat]
        },
        properties: {
          confidence: row.confidence,
          brightness: row.brightness,
          satellite: row.satellite
        }
      }
    })
    .filter((feature: any) => feature !== null) // Remove invalid features

  return {
    type: 'FeatureCollection',
    features
  }
}
