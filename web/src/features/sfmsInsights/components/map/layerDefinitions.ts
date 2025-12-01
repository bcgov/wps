import { PMTilesVectorSource } from 'ol-pmtiles'
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL, PMTILES_BUCKET, PSU_BUCKET } from 'utils/env'
import { fuelCOGColourExpression, snowStyler } from '@/features/sfmsInsights/components/map/sfmsFeatureStylers'
import VectorTileLayer from 'ol/layer/VectorTile'
import { DateTime } from 'luxon'
import WebGLTile from 'ol/layer/WebGLTile'
import GeoTIFF from 'ol/source/GeoTIFF'
import VectorSource from 'ol/source/VectorTile'
import MVT from "ol/format/MVT"
import { applyStyle } from "ol-mapbox-style"

export const BASEMAP_LAYER_NAME = "basemapLayer";
export const SNOW_LAYER_NAME = 'snowVector'

const basemapSource = new VectorSource({
  format: new MVT({ layerName: "mvt:layer" }),
  url: BASEMAP_TILE_URL,
});

export const createBasemapLayer = async () => {
  const basemapLayer = new VectorTileLayer({
    source: basemapSource
  });
  basemapLayer.set("name", BASEMAP_LAYER_NAME);
  // Fetch the style json from ArcGIS Online
  const response = await fetch(BASEMAP_STYLE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  const style = await response.json();
  applyStyle(basemapLayer, style, { updateSource: false });
  return basemapLayer;
};

export const getSnowPMTilesLayer = (snowDate: DateTime) => {
  const url = `${PMTILES_BUCKET}snow/${snowDate.toISODate()}/snowCoverage${snowDate.toISODate({ format: 'basic' })}.pmtiles`
  const snowPMTilesSource = new PMTilesVectorSource({
    url
  })
  const snowPMTilesLayer = new VectorTileLayer({
    source: snowPMTilesSource,
    style: snowStyler,
    zIndex: 52,
    minZoom: 4,
    properties: { name: SNOW_LAYER_NAME }
  })
  return snowPMTilesLayer
}

export const fuelGridCOG = new GeoTIFF({
  sources: [
    {
      url: `${PSU_BUCKET}cog/fbp2025_500m_cog.tif`
    }
  ],
  interpolate: false,
  normalize: false // important, otherwise the values will be scaled to 0-1
})

export const fuelCOGTiles = new WebGLTile({
  source: fuelGridCOG,
  zIndex: 51,
  opacity: 0.6,
  style: {
    color: fuelCOGColourExpression()
  }
})
