import { RunType } from "@/api/fbaAPI";
import { IPMTilesCache } from "@/utils/pmtilesCache";
import { PMTilesFileVectorSource } from "@/utils/pmtilesVectorSource";
import { DateTime } from "luxon";
import { PMTiles } from "pmtiles";
import sinon from "sinon";

describe("pmTilesVectorSource", () => {
  let sandbox: sinon.SinonSandbox;
  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });
  afterEach(() => {
    sandbox.restore();
  });
  const buildPMTilesTestCache = () => {
    return {
      loadPMTiles: function (
        filename: string,
        fetchAndStoreCallback?: () => Promise<PMTiles | undefined>
      ): Promise<PMTiles | undefined> {
        console.log("loadPMTiles called", filename, fetchAndStoreCallback);
        return Promise.resolve(undefined);
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
        return Promise.resolve(undefined);
      },
    };
  };
  it("should attempt to load static pmtiles upon creation", async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache();
    const pmTilesCacheSpy = sandbox.spy(testCache);

    await PMTilesFileVectorSource.createStaticLayer(testCache, {
      filename: "test.pmtiles",
    });
    sinon.assert.calledOnce(pmTilesCacheSpy.loadPMTiles);
    sinon.assert.notCalled(pmTilesCacheSpy.loadHFIPMTiles);
  });

  it("should attempt to load hfi pmtiles upon creation", async () => {
    const testCache: IPMTilesCache = buildPMTilesTestCache();
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
});
