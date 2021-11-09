import EsriJSON from 'ol/format/EsriJSON'
import VectorSource from 'ol/source/Vector'
import Projection from 'ol/proj/Projection'
import Geometry from 'ol/geom/Geometry'
import axios from 'axios'

export type FireLayer = '2' | '8'
export const fireCenterLayer: FireLayer = '2'
export const fireZoneLayer: FireLayer = '8'

const fireCenterUrl =
  'https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/'

/**
 * Retrieves fire center polygons from maps.gov.bc.ca arcserver
 * Requests are made dynamically as an openlayers vector source.
 *
 * @param extent Current extent of the view
 * @param projection Current projection
 * @param vectorSource the source to add the requested features to
 */
export const getFireCenterVectorSource = async (
  layer: FireLayer,
  extent: number[],
  projection: Projection,
  vectorSource: VectorSource<Geometry>
): Promise<void> => {
  const esriJsonFormat = new EsriJSON()

  const url =
    '/query/?f=json&' +
    'returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=' +
    // Extent, see description here:
    // https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
    encodeURIComponent(
      '{"xmin":' +
        extent[0] +
        ',"ymin":' +
        extent[1] +
        ',"xmax":' +
        extent[2] +
        ',"ymax":' +
        extent[3] +
        ',"spatialReference":{"wkid":102100}}'
    ) +
    // Quantization Parameter, see description here:
    // https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer-.htm
    encodeURIComponent(
      `
      {
        "mode": "view", "originPosition": "upperLeft", "tolerance": ${1222.992452562501},
        "extent":
          { "type":"extent",
            "xmin":${extent[0]},
            "ymin":${extent[1]},
            "xmax":${extent[2]},
            "ymax":${extent[3]},
            "spatialReference":{"wkid":102100}}
      }
      `
    ) +
    '&geometryType=esriGeometryEnvelope&inSR=102100&outFields=*' +
    '&outSR=102100'

  const axiosInstance = axios.create({
    baseURL: fireCenterUrl + layer
  })
  const { data } = await axiosInstance.get(url)
  const features = esriJsonFormat.readFeatures(data, {
    featureProjection: projection
  })
  if (features.length > 0) {
    vectorSource.addFeatures(features)
  }
}
