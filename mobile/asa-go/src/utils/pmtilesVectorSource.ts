import { Tile } from "ol";
import RenderFeature from "ol/render/Feature";
import VectorTile, {
  type Options as VectorTileSourceOptions,
  default as VectorTileSource,
} from "ol/source/VectorTile";
import { createXYZ } from "ol/tilegrid";
import TileState from "ol/TileState";
import { PMTiles } from "pmtiles";
import { MVT } from "ol/format";
import { IPMTilesCache } from "@/utils/pmtilesCache";
import { DateTime } from "luxon";
import { RunType } from "@/api/fbaAPI";
import { isUndefined } from "lodash";

export type PMTilesFileVectorOptions = VectorTileSourceOptions & {
  filename: string;
};

export type HFIPMTilesFileVectorOptions = VectorTileSourceOptions &
  PMTilesFileVectorOptions & {
    for_date: DateTime;
    run_type: RunType;
    run_date: DateTime;
  };

export class PMTilesFileVectorSource extends VectorTileSource {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  private pmtiles_: PMTiles;

  tileLoadFunction = (tile: Tile, url: string) => {
    const vtile = tile as unknown as VectorTile;
    const re = new RegExp(/pmtiles:\/\/(\d+)\/(\d+)\/(\d+)/);
    const result = url.match(re);

    if (!(result && result.length >= 4)) {
      throw new Error("Could not parse tile URL");
    }
    const z = +result[1];
    const x = +result[2];
    const y = +result[3];

    tile.setState(TileState.LOADING); // Set state to LOADING

    // Use the PMTiles getZxy method to fetch the tile data
    this.pmtiles_
      .getZxy(z, x, y)
      .then((tile_result) => {
        if (tile_result) {
          const format = new MVT({layerName: 'mvt:layer'}); // Create the MVT format
          const features = format.readFeatures(tile_result.data, {
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            extent: vtile.extent,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            featureProjection: vtile.projection,
          });

          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          vtile.setFeatures(features); // Set the features on the tile (which can now handle vector data)
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          vtile.setState(TileState.LOADED); // Mark the tile as loaded
        } else {
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          vtile.setFeatures([]);
          // eslint-disable-next-line @typescript-eslint/ban-ts-comment
          // @ts-ignore
          vtile.setState(TileState.EMPTY); // Mark the tile as empty if no data is found
        }
      })
      .catch((err) => {
        console.log(err);
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        vtile.setFeatures([]);
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        vtile.setState(TileState.ERROR); // Mark the tile as error if the loading fails
      });
  };

  constructor(options: VectorTileSourceOptions<RenderFeature>) {
    super({
      ...options,
      state: "loading",
      url: "pmtiles://{z}/{x}/{y}", // only used for parsing out the z, x, y parameters when tile loading
      format: options.format || new MVT({layerName: 'mvt:layer'}),
    });
  }

  // Static async factory method
  static async createStaticLayer(
    pmtilesCache: IPMTilesCache,
    options: PMTilesFileVectorOptions
  ) {
    const instance = new PMTilesFileVectorSource(options);

    // Perform asynchronous initialization (e.g., loading PMTiles)
    await instance.initStaticLayer(pmtilesCache, options);

    return instance;
  }

  async initStaticLayer(
    pmtilesCache: IPMTilesCache,
    options: PMTilesFileVectorOptions
  ) {
    try {
      console.log(`Attempting to read ${options.filename}`);

      const pmtiles = await pmtilesCache.loadPMTiles(options.filename);

      await this.initTileGrid(pmtiles);
    } catch (error) {
      console.error("Error loading PMTiles file:", error);
      this.setState("error");
    }
  }

  async initTileGrid(pmtiles?: PMTiles) {
    if (!isUndefined(pmtiles)) {
      this.pmtiles_ = pmtiles;
    } else {
      throw Error("Unable to initialize pmtiles");
    }
    const header = await this.pmtiles_.getHeader();

    this.tileGrid = createXYZ({
      maxZoom: header.maxZoom,
      minZoom: header.minZoom,
      tileSize: 512,
    });

    this.setTileLoadFunction(this.tileLoadFunction);
    this.setState("ready");
  }

  static async createBasemapSource(
    pmtilesCache: IPMTilesCache,
    options: PMTilesFileVectorOptions
  ) {
    const instance = new PMTilesFileVectorSource(options)
    await instance.initBasemapSource(pmtilesCache, options)
    return instance
  }

  async initBasemapSource(pmtilesCache: IPMTilesCache, options: PMTilesFileVectorOptions){
    try {
      console.log("Attempting to download offline pmtiles basemap assets.")
      const pmtiles = await pmtilesCache.loadPMTiles(options.filename);

      await this.initTileGrid(pmtiles);

    } catch (error) {
      console.error("Error loading PMTiles file:", error);
      this.setState("error");
    }
  }

  static async createHFILayer(
    pmtilesCache: IPMTilesCache,
    options: HFIPMTilesFileVectorOptions
  ) {
    const instance = new PMTilesFileVectorSource(options);

    await instance.initHFILayer(pmtilesCache, options);

    return instance;
  }

  async initHFILayer(
    pmtilesCache: IPMTilesCache,
    options: HFIPMTilesFileVectorOptions
  ) {
    try {
      console.log(`Attempting to read ${options.filename}`);

      const pmtiles = await pmtilesCache.loadHFIPMTiles(
        options.for_date,
        options.run_type,
        options.run_date,
        options.filename
      );
      await this.initTileGrid(pmtiles);
    } catch (error) {
      console.error("Error loading PMTiles file:", error);
      this.setState("error");
    }
  }
}
