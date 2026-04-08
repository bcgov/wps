import axios from './axios'

/** Retrieve 4-panel chart from S3 storage as a blob via the WPS API as a proxy.
 *
 * @param chartKey - An S3 key for a 4-panel chart.
 * @returns A blob representation of the 4-panel chart.
 */
export async function getWxChart(chartKey: string): Promise<Blob> {
  const { data } = await axios.get<Blob>(`/wx-object-store-proxy/${chartKey}`, { responseType: 'blob' })
  return data
}
