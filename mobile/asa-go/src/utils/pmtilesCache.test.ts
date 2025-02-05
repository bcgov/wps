import { RunType } from "@/api/fbaAPI";
import { PMTilesCache } from "@/utils/pmtilesCache";
import { PluginListenerHandle } from "@capacitor/core";
import {
  AppendFileOptions,
  CopyOptions,
  CopyResult,
  DeleteFileOptions,
  DownloadFileOptions,
  DownloadFileResult,
  FilesystemPlugin,
  GetUriOptions,
  GetUriResult,
  MkdirOptions,
  PermissionStatus,
  ProgressListener,
  ReaddirOptions,
  ReaddirResult,
  ReadFileOptions,
  ReadFileResult,
  RenameOptions,
  RmdirOptions,
  StatOptions,
  StatResult,
  WriteFileOptions,
  WriteFileResult,
} from "@capacitor/filesystem";
import { DateTime } from "luxon";

import sinon from "sinon";

export class MockFilesystem implements FilesystemPlugin {
  readFile(options: ReadFileOptions): Promise<ReadFileResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ data: "" });
  }
  writeFile(options: WriteFileOptions): Promise<WriteFileResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ uri: "" });
  }
  appendFile(options: AppendFileOptions): Promise<void> {
    console.log("Method not implemented.", options);
    return Promise.resolve();
  }
  deleteFile(options: DeleteFileOptions): Promise<void> {
    console.log("Method not implemented.", options);
    return Promise.resolve();
  }
  mkdir(options: MkdirOptions): Promise<void> {
    console.log("Method not implemented.", options);
    return Promise.resolve();
  }
  rmdir(options: RmdirOptions): Promise<void> {
    console.log("Method not implemented.", options);
    return Promise.resolve();
  }
  readdir(options: ReaddirOptions): Promise<ReaddirResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ files: [] });
  }
  getUri(options: GetUriOptions): Promise<GetUriResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ uri: "" });
  }
  stat(options: StatOptions): Promise<StatResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ type: "file", size: 0, mtime: 0, uri: "" });
  }
  rename(options: RenameOptions): Promise<void> {
    console.log("Method not implemented.", options);
    return Promise.resolve();
  }
  copy(options: CopyOptions): Promise<CopyResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({ uri: "" });
  }
  checkPermissions(): Promise<PermissionStatus> {
    console.log("Method not implemented.");
    return Promise.resolve({ publicStorage: "granted" });
  }
  requestPermissions(): Promise<PermissionStatus> {
    console.log("Method not implemented.");
    return Promise.resolve({ publicStorage: "granted" });
  }
  downloadFile(options: DownloadFileOptions): Promise<DownloadFileResult> {
    console.log("Method not implemented.", options);
    return Promise.resolve({});
  }
  addListener(
    eventName: "progress",
    listenerFunc: ProgressListener
  ): Promise<PluginListenerHandle> {
    console.log("Method not implemented.", eventName, listenerFunc);
    return Promise.resolve({
      remove: () => Promise.resolve(),
    });
  }
  removeAllListeners(): Promise<void> {
    console.log("Method not implemented.");
    return Promise.resolve();
  }
}

describe("pmtilesCache", () => {
  let sandbox: sinon.SinonSandbox;
  beforeEach(() => {
    sandbox = sinon.createSandbox();
  });
  afterEach(() => {
    sandbox.restore();
  });

  it("should attempt to load stored static pmtiles", async () => {
    const mockFs = new MockFilesystem();

    const stubRead = sandbox.stub(mockFs, "readFile");
    stubRead.resolves({ data: btoa("mocked file content") });
    const testCache = new PMTilesCache(mockFs);
    await testCache.loadPMTiles("test.pmtiles");
    sinon.assert.calledOnce(stubRead);
  });

  it("should attempt to load stored static pmtiles first then fallback to requesting them", async () => {
    const mockFs = new MockFilesystem();
    const stubRead = sandbox
      .stub(mockFs, "readFile")
      .rejects(new Error("Read failed"));

    const stubFetch = sandbox.stub().rejects(new Error("Fetch failed"));
    const testCache = new PMTilesCache(mockFs);
    await testCache.loadPMTiles("test.pmtiles", stubFetch);
    sinon.assert.calledThrice(stubFetch);
    sinon.assert.callOrder(stubRead, stubFetch, stubFetch, stubFetch);
  });

  it("should attempt to load stored hfi pmtiles", async () => {
    const mockFs = new MockFilesystem();

    const stubRead = sandbox.stub(mockFs, "readFile");
    stubRead.resolves({ data: btoa("mocked file content") });
    const testCache = new PMTilesCache(mockFs);
    await testCache.loadHFIPMTiles(
      DateTime.fromISO("2016-05-25T09:08:34.123"),
      RunType.FORECAST,
      DateTime.fromISO("2016-05-25T09:08:34.123"),
      "test.pmtiles"
    );
    sinon.assert.calledOnce(stubRead);
  });

  it("should attempt to load stored hfi pmtiles first then fallback to requesting them", async () => {
    const mockFs = new MockFilesystem();
    const stubRead = sandbox
      .stub(mockFs, "readFile")
      .rejects(new Error("Read failed"));

    const stubFetch = sandbox.stub().rejects(new Error("Fetch failed"));
    const testCache = new PMTilesCache(mockFs);
    await testCache.loadHFIPMTiles(
      DateTime.fromISO("2016-05-25T09:08:34.123"),
      RunType.FORECAST,
      DateTime.fromISO("2016-05-25T09:08:34.123"),
      "test.pmtiles",
      stubFetch
    );
    sinon.assert.calledThrice(stubFetch);
    sinon.assert.callOrder(stubRead, stubFetch, stubFetch, stubFetch);
  });
});
