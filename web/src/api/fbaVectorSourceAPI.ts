import EsriJSON from 'ol/format/EsriJSON'
import VectorSource from 'ol/source/Vector'
import * as $ from 'jquery'
import * as ol from 'ol'
import Projection from 'ol/proj/Projection'
import Geometry from 'ol/geom/Geometry'

const fireCenterUrl =
  'https://maps.gov.bc.ca/arcserver/rest/services/whse/bcgw_pub_whse_legal_admin_boundaries/MapServer/'
const outlineLayer = '2'
/**
 * Retrieves fire center polygons from maps.gov.bc.ca arcserver
 * Requests are made dynamically as an openlayers vector source.
 *
 * @param extent Current extent of the view
 * @param projection Current projection
 * @param vectorSource the source to add the requested features to
 * @param success success callback
 * @returns
 */
export const getFireCenterVectorSource = async (
  extent: number[],
  projection: Projection,
  vectorSource: VectorSource<Geometry>,
  success: ((arg0: ol.Feature<Geometry>[]) => void) | undefined
): Promise<ol.Feature<Geometry>[] | undefined> => {
  const esriJsonFormat = new EsriJSON()

  const url =
    fireCenterUrl +
    outlineLayer +
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

  // TODO: Get working with axios (CORS errors)
  return $.ajax({
    url: url,
    dataType: 'jsonp',
    success: response => {
      // dataProjection will be read from document
      const features = esriJsonFormat.readFeatures(response, {
        featureProjection: projection
      })
      if (features.length > 0) {
        vectorSource.addFeatures(features)
      }
      if (success) {
        success(features)
      }
    }
  })
}
