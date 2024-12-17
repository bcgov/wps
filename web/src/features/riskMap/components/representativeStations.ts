import { GeoJsonStation, DetailedGeoJsonStation, FirePerimeterStation } from '@/api/stationAPI'
import { FireShapeStation } from '@/features/riskMap/slices/representativeStationSlice'
import { groupBy } from 'lodash'

export const decorateRepStations = (
  stations: GeoJsonStation[] | DetailedGeoJsonStation[],
  repStations: FireShapeStation[]
) => {
  const stationCode2FireNumbers = groupBy(repStations, 'station_code')
  const firePerimStations: FirePerimeterStation[] = stations.map(station => {
    const fireShapeStation = stationCode2FireNumbers[station.properties.code]
    const firePerimStation: FirePerimeterStation = {
      ...station,
      properties: {
        code: station.properties.code,
        name: station.properties.name,
        fire_numbers: fireShapeStation.map(fireNum => fireNum.fire_number)
      }
    }
    return firePerimStation
  })
  return firePerimStations
}
