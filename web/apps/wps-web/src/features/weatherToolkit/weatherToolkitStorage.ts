export const WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY = 'wps-weather-toolkit-chart-expanded'

export const readChartExpanded = () => {
  try {
    const storedValue = localStorage.getItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY)
    return storedValue === 'true'
  } catch {
    return false
  }
}

export const storeChartExpanded = (chartExpanded: boolean) => {
  try {
    localStorage.setItem(WEATHER_TOOLKIT_CHART_EXPANDED_STORAGE_KEY, String(chartExpanded))
  } catch {
    return
  }
}
