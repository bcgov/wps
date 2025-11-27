import { localBasemapStyle } from "@/components/map/localBasemapStyle";
import { hfiStyler } from "@/featureStylers";
import { BASEMAP_STYLE_URL, BASEMAP_TILE_URL } from "@/utils/env";
import { PMTilesCache } from "@/utils/pmtilesCache";
import {
  HFIPMTilesFileVectorOptions,
  PMTilesFileVectorSource,
} from "@/utils/pmtilesVectorSource";
import { Filesystem } from "@capacitor/filesystem";
import { applyStyle } from "ol-mapbox-style";
import MVT from "ol/format/MVT";
import VectorTileLayer from "ol/layer/VectorTile";
import VectorSource from "ol/source/VectorTile";

export const BASEMAP_LAYER_NAME = "basemapLayer";
export const LOCAL_BASEMAP_LAYER_NAME = "localBasemapLayer";
export const HFI_LAYER_NAME = "hfiVectorLayer";
export const ZONE_STATUS_LAYER_NAME = "fireShapeVector";

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

export const createLocalBasemapVectorLayer = async () => {
  const localBasemapSource = await PMTilesFileVectorSource.createBasemapSource(
    new PMTilesCache(Filesystem),
    {
      filename: "bc_20250326_z6.pmtiles",
    }
  );
  const localBasemapLayer = new VectorTileLayer({
    source: localBasemapSource,
    zIndex: 10,
  });
  localBasemapLayer.set("name", LOCAL_BASEMAP_LAYER_NAME);
  applyStyle(localBasemapLayer, localBasemapStyle, { updateSource: false });
  return localBasemapLayer;
};

export const createHFILayer = async (
  options: HFIPMTilesFileVectorOptions,
  visible: boolean = true
): Promise<VectorTileLayer> => {
  const hfiVectorSource = await PMTilesFileVectorSource.createHFILayer(
    new PMTilesCache(Filesystem),
    {
      filename: options.filename,
      for_date: options.for_date,
      run_type: options.run_type,
      run_date: options.run_date,
    }
  );
  return new VectorTileLayer({
    source: hfiVectorSource,
    style: hfiStyler,
    zIndex: 51,
    properties: { name: HFI_LAYER_NAME },
    visible: visible,
  });
};
