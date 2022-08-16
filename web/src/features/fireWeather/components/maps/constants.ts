import XYZ from 'ol/source/XYZ'
import { RASTER_SERVER_BASE_URL } from 'utils/env'

export const BC_ROAD_BASE_MAP_SERVER_URL = 'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

// Static source is allocated since our tile source does not change and
// a new source is not allocated every time WeatherMap is re-rendered,
// which causes the TileLayer to re-render.
export const source = new XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
  // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
  // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
  attributions: 'Government of British Columbia, DataBC, GeoBC'
})

// This "monochrome" source doesn't have the level of detail that the roads layers does,
// but it's much cleaner.
export const monochromeSource = new XYZ({
  url: `https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`,
  attributions: ['Esri', '© OpenStreetMap contributors', 'HERE', 'Garmin', 'USGS', 'EPA', 'NPS', 'NRCan']
})

export const ftlSource = new XYZ({
  url: `${RASTER_SERVER_BASE_URL}/tile/{z}/{x}/{y}?path=gpdqha/ftl/ftl_2018_cloudoptimized.tif&source=ftl`,
  imageSmoothing: true
})

export const sfmsFtlSource = new XYZ({
  url: `${RASTER_SERVER_BASE_URL}/tile/{z}/{x}/{y}?path=gpdqha/sfms/cog/static/cog_fbp2021.tif&source=ftl`,
  imageSmoothing: true
})
