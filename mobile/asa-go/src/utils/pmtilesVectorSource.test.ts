import { RunType } from "@/api/fbaAPI";
import { IPMTilesCache } from "@/utils/pmtilesCache";
import { PMTilesFileVectorSource } from "@/utils/pmtilesVectorSource";
import { DateTime } from "luxon";
import {
  Cache,
  Compression,
  DecompressFunc,
  Header,
  PMTiles,
  RangeResponse,
  Source,
  TileType,
} from "pmtiles";
import sinon from "sinon";
import { assert } from "vitest";

const testPMTilesHeader: Header = {
  specVersion: 0,
  rootDirectoryOffset: 0,
  rootDirectoryLength: 0,
  jsonMetadataOffset: 0,
  jsonMetadataLength: 0,
  leafDirectoryOffset: 0,
  tileDataOffset: 0,
  numAddressedTiles: 0,
  numTileEntries: 0,
  numTileContents: 0,
  clustered: false,
  internalCompression: Compression.Unknown,
  tileCompression: Compression.Unknown,
  tileType: TileType.Unknown,
  minZoom: 0,
  maxZoom: 0,
  minLon: 0,
  minLat: 0,
  maxLon: 0,
  maxLat: 0,
  centerZoom: 0,
  centerLon: 0,
  centerLat: 0,
};

class TestPMTiles implements PMTiles {
  source!: Source;
  cache!: Cache;
  decompress!: DecompressFunc;
  getHeader(): Promise<Header> {
    console.log("getHeader called");
    return Promise.resolve(testPMTilesHeader);
  }
  getZxyAttempt(
    z: number,
    x: number,
    y: number,
    signal?: AbortSignal
  ): Promise<RangeResponse | undefined> {
    console.log("getZxyAttempt called", z, x, y, signal);
    return Promise.resolve(undefined);
  }
  getZxy(
    z: number,
    x: number,
    y: number,
    signal?: AbortSignal
  ): Promise<RangeResponse | undefined> {
    console.log("getZxy called", z, x, y, signal);
    return Promise.resolve(undefined);
  }
  getMetadataAttempt(): Promise<unknown> {
    console.log("getMetadataAttempt called");
    return Promise.resolve();
  }
  getMetadata(): Promise<unknown> {
    console.log("getMetadata called");
    return Promise.resolve();
  }
  getTileJson(baseTilesUrl: string): Promise<unknown> {
    console.log("getTileJSON called", baseTilesUrl);
    return Promise.resolve();
  }
}

describe("pmTilesVectorSource", () => {
  let sandbox: sinon.SinonSandbox;
  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });
  afterEach(() => {
    sandbox.restore();
  });

  const buildPMTilesTestCache = (pmtiles?: PMTiles) => {
    return {
      loadPMTiles: function (
        filename: string,
        fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
      ): Promise<PMTiles | undefined> {
        console.log("loadPMTiles called", filename, fetchAndStoreCallback);
        return Promise.resolve(pmtiles);
      },
      loadHFIPMTiles: function (
        for_date: DateTime,
        run_type: RunType,
        run_date: DateTime,
        filename: string
      ): Promise<PMTiles | undefined> {
        console.log(
          "loadPMTiles called",
          for_date,
          run_type,
          run_date,
          filename
        );
        return Promise.resolve(pmtiles);
      },
    };
  };
  it("should attempt to load static pmtiles upon creation", async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles());
    const pmTilesCacheSpy = sandbox.spy(testCache);

    await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: "test.pmtiles",
    });
    sinon.assert.calledOnce(pmTilesCacheSpy.loadPMTiles);
    sinon.assert.notCalled(pmTilesCacheSpy.loadHFIPMTiles);
  });

  it("should attempt to load hfi pmtiles upon creation", async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles());
    const pmTilesCacheSpy = sandbox.spy(testCache);

    await PMTilesFileVectorSource.createHFILayer(testCache, {
      filename: "test.pmtiles",
      for_date: DateTime.fromISO("2016-05-25T09:08:34.123"),
      run_type: RunType.FORECAST,
      run_date: DateTime.fromISO("2016-05-25T09:08:34.123"),
    });
    sinon.assert.calledOnce(pmTilesCacheSpy.loadHFIPMTiles);
    sinon.assert.notCalled(pmTilesCacheSpy.loadPMTiles);
  });

  it("should set tile status ready once initialized", async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache(new TestPMTiles());
    const instance = await PMTilesFileVectorSource.createHFILayer(testCache, {
      filename: "test.pmtiles",
      for_date: DateTime.fromISO("2016-05-25T09:08:34.123"),
      run_type: RunType.FORECAST,
      run_date: DateTime.fromISO("2016-05-25T09:08:34.123"),
    });
    const tileGrid = instance.getTileGrid();
    assert(tileGrid !== null);
    assert(tileGrid.getMaxZoom() === testPMTilesHeader.maxZoom);
    assert(tileGrid.getMinZoom() === testPMTilesHeader.minZoom);
    assert(instance.getState() === "ready");
  });
});
