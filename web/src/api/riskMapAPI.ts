import axios from 'axios'
import { DateTime } from 'luxon'
import { FIRMS_KEY } from 'utils/env'

export async function getHotSpots(dateOfInterest: DateTime): Promise<string> {
  const url = `https://firms.modaps.eosdis.nasa.gov/api/area/csv/${FIRMS_KEY}/MODIS_NRT/-139,48,-114,60/2/${dateOfInterest.toISODate()}`
  const { data } = await axios.get(url)
  return data
}
