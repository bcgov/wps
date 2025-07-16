import VectorTileLayer from "ol/layer/VectorTile";
import { applyStyle } from "ol-mapbox-style";
import { BC_ROAD_BASE_MAP_SERVER_URL } from "utils/constants";
import XYZ from "ol/source/XYZ";
import TileLayer from "ol/layer/Tile";
import {
  HFIPMTilesFileVectorOptions,
  PMTilesFileVectorSource,
} from "@/utils/pmtilesVectorSource";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { Filesystem } from "@capacitor/filesystem";
import { localBasemapStyle } from "@/components/map/localBasemapStyle";
import { hfiStyler } from "@/featureStylers";

export const BASEMAP_LAYER_NAME = "basemapLayer";
export const LOCAL_BASEMAP_LAYER_NAME = "localBasemapLayer";

// Static source is allocated since our tile source does not change and
// a new source is not allocated every time WeatherMap is re-rendered,
// which causes the TileLayer to re-render.
const basemapSource = new XYZ({
  url: `${BC_ROAD_BASE_MAP_SERVER_URL}/tile/{z}/{y}/{x}`,
  // Normally we would get attribution text from `${BC_ROAD_BASE_MAP_SERVER_URL}?f=pjson`
  // however this endpoint only allows the origin of http://localhost:3000, so the text has been just copied from that link
  // attributions: 'Government of British Columbia, DataBC, GeoBC'
});

export const createBasemapLayer = () => {
  const basemapLayer = new TileLayer({ source: basemapSource, zIndex: 20 });
  basemapLayer.set("name", BASEMAP_LAYER_NAME);
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
  zIndex: number = 51
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
    zIndex,
    properties: { name: `hfiLayer_${options.for_date}` },
  });
};
