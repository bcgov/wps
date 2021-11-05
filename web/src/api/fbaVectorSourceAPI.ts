import EsriJSON from 'ol/format/EsriJSON'
import VectorSource from 'ol/source/Vector'
import * as $ from 'jquery'
import * as ol from 'ol'
import Projection from 'ol/proj/Projection'
import Geometry from 'ol/geom/Geometry'

const serviceUrl =
  'https://sampleserver3.arcgisonline.com/ArcGIS/rest/services/' +
  'Petroleum/KSFields/FeatureServer/'
const layer = '0'
export async function getFireCenterVectorSource(
  extent: number[],
  projection: Projection,
  vectorSource: VectorSource<Geometry>,
  success: ((arg0: ol.Feature<Geometry>[]) => void) | undefined
): Promise<ol.Feature<Geometry>[] | undefined> {
  const esriJsonFormat = new EsriJSON()

  const url =
    serviceUrl +
    layer +
    '/query/?f=json&' +
    'returnGeometry=true&spatialRel=esriSpatialRelIntersects&geometry=' +
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
