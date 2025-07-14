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
import { Map } from "ol";
import { FireCenter, FireShape } from "@/api/fbaAPI";
import {
  fireCentreLabelStyler,
  fireCentreLineStyler,
  fireShapeLabelStyler,
  hfiStyler,
} from "@/featureStylers";

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

export const loadStaticPMTilesLayers = async (
  mapObject: Map,
  fireZoneFileLayer: VectorTileLayer,
  selectedFireCenter: FireCenter | undefined,
  selectedFireShape: FireShape | undefined,
  setLocalBasemapVectorLayer: React.Dispatch<
    React.SetStateAction<VectorTileLayer>
  >
) => {
  const fireCentresSource = await PMTilesFileVectorSource.createStaticLayer(
    new PMTilesCache(Filesystem),
    { filename: "fireCentres.pmtiles" }
  );

  const fireCentreLabelVectorSource =
    await PMTilesFileVectorSource.createStaticLayer(
      new PMTilesCache(Filesystem),
      { filename: "fireCentreLabels.pmtiles" }
    );

  const fireZoneSource = await PMTilesFileVectorSource.createStaticLayer(
    new PMTilesCache(Filesystem),
    { filename: "fireZoneUnits.pmtiles" }
  );
  fireZoneFileLayer.setSource(fireZoneSource);

  const fireZoneLabelVectorSource =
    await PMTilesFileVectorSource.createStaticLayer(
      new PMTilesCache(Filesystem),
      { filename: "fireZoneUnitLabels.pmtiles" }
    );

  const fireCentreFileLayer = new VectorTileLayer({
    source: fireCentresSource,
    style: fireCentreLineStyler(selectedFireCenter),
    zIndex: 52,
  });

  const fireCentreLabelsFileLayer = new VectorTileLayer({
    source: fireCentreLabelVectorSource,
    style: fireCentreLabelStyler,
    zIndex: 100,
    maxZoom: 6,
  });

  const fireZoneLabelFileLayer = new VectorTileLayer({
    source: fireZoneLabelVectorSource,
    declutter: true,
    style: fireShapeLabelStyler(selectedFireShape),
    zIndex: 99,
    minZoom: 6,
  });

  const localBasemapLayer = await createLocalBasemapVectorLayer();
  setLocalBasemapVectorLayer(localBasemapLayer);

  mapObject.addLayer(fireCentreFileLayer);
  mapObject.addLayer(fireCentreLabelsFileLayer);
  mapObject.addLayer(fireZoneFileLayer);
  mapObject.addLayer(fireZoneLabelFileLayer);
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
