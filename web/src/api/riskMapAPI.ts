import axios from 'axios'
import { FIRMS_KEY } from 'utils/env'

export async function getHotSpots(dateOfInterest: Date, daysAfter: number): Promise<string> {
  const url = `https://firms.modaps.eosdis.nasa.gov/api/area/csv/${FIRMS_KEY}/MODIS_NRT/-139,48,-114,60/${daysAfter}/${dateOfInterest.toISOString().slice(0, 10)}`
  const { data } = await axios.get(url)
  return data
}
