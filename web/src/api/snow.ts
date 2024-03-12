import axios from 'api/axios'
import { DateTime } from 'luxon'

enum SnowSource {
  VIIRS = 'viirs'
}

// The shape of processed snow data.
interface ProcessedSnowPayload {
  for_date: string
  processed_date: string
  snow_source: SnowSource
}

// Response object from our API.
interface ProcessedSnowResponse {
  processed_snow: ProcessedSnowPayload
}

// Client side representation of processed snow data.
export interface ProcessedSnow {
  forDate: DateTime
  processedDate: DateTime
  snowSource: SnowSource
}

export async function getMostRecentProcessedSnowByDate(forDate: DateTime): Promise<ProcessedSnow | null> {
  if (!forDate) {
    return null
  }
  const url = `snow/most-recent-by-date/${forDate.toISODate()}`
  const { data } = await axios.get<ProcessedSnowResponse | null>(url, {})
  if (data) {
    const processedSnow = data.processed_snow
    return {
      forDate: DateTime.fromISO(processedSnow.for_date),
      processedDate: DateTime.fromISO(processedSnow.processed_date),
      snowSource: processedSnow.snow_source
    }
  }
  return data
}
