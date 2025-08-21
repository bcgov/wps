import { FireShapeArea } from "@/api/fbaAPI";
import { fireShapeStyler } from "@/featureStylers";
import { ZONE_STATUS_LAYER_NAME, HFI_LAYER_NAME } from "@/layerDefinitions";
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem";
import { cloneDeep } from "lodash";
import VectorTileLayer from "ol/layer/VectorTile";

export interface LayerVisibility {
  [layerName: string]: boolean;
}

export const defaultLayerVisibility: LayerVisibility = {
  [ZONE_STATUS_LAYER_NAME]: true,
  [HFI_LAYER_NAME]: true,
};

const LAYER_VISIBILITY_FILE = "layer_visibility.json";

export const loadLayerVisibility = async (
  defaultVisibility: LayerVisibility
): Promise<LayerVisibility> => {
  try {
    const result = await Filesystem.readFile({
      path: LAYER_VISIBILITY_FILE,
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });
    const parsed: LayerVisibility = JSON.parse(result.data as string);
    return { ...defaultVisibility, ...parsed, [ZONE_STATUS_LAYER_NAME]: true };
  } catch {
    // file may not exist yet; use defaults
    return defaultVisibility;
  }
};

export const saveLayerVisibility = async (
  visibility: LayerVisibility
): Promise<void> => {
  await Filesystem.writeFile({
    path: LAYER_VISIBILITY_FILE,
    data: JSON.stringify(visibility),
    directory: Directory.Data,
    encoding: Encoding.UTF8,
  });
};

export const setZoneStatusLayerVisibility = (
  layer: VectorTileLayer,
  fireShapeAreas: FireShapeArea[],
  advisoryThreshold: number,
  visible: boolean
): void => {
  layer.setStyle(
    fireShapeStyler(cloneDeep(fireShapeAreas), advisoryThreshold, visible)
  );
  layer.changed();
};

export const setDefaultLayerVisibility = (
  layers: Record<string, VectorTileLayer | null>,
  layerName: string,
  visible: boolean
): void => {
  const layer = layers[layerName];
  if (layer) {
    layer.setVisible(visible);
  }
};
