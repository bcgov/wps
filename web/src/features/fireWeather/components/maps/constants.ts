import XYZ from 'ol/source/XYZ'

export const BC_ROAD_BASE_MAP_SERVER_URL =
  'https://maps.gov.bc.ca/arcgis/rest/services/province/roads_wm/MapServer'

// Static source is allocated since our tile source does not change and
// a new source is not allocated every time WeatherMap is re-rendered,
// which causes the TileLayer to re-render.
export const source = new XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
  // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
  // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
  attributions: 'Government of British Columbia, DataBC, GeoBC'
})

export const monochrome_source = new XYZ({
  url: `https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}`,
  attributions: 'ARCGIS'
})
