import { RunType } from "@/api/fbaAPI";
import { fetchPMTiles } from "@/api/pmtilesAPI";
import { Directory, Encoding, FilesystemPlugin } from "@capacitor/filesystem";
import { DateTime } from "luxon";
import { FileSource, PMTiles } from "pmtiles";

export class PMTilesCache {
  constructor(private readonly fileSystem: FilesystemPlugin) {}
  private readonly downloadAndStorePMTiles = async (
    for_date: DateTime,
    run_type: RunType,
    run_date: DateTime,
    filename: string
  ) => {
    try {
      const blob = await fetchPMTiles(for_date, run_type, run_date);
      const serialized = await this.serialize(blob);

      await this.fileSystem.writeFile({
        path: filename,
        data: serialized,
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });

      console.log(`PMTiles stored: ${filename}`);
    } catch (error) {
      console.error("Error storing PMTiles:", error);
    }
  };

  private readonly blobToBase64 = async (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
    });
  };

  private readonly base64ToBlob = (
    base64: string,
    contentType = "application/octet-stream"
  ) => {
    const byteCharacters = atob(base64.split(",")[1]); // Remove Base64 prefix
    const byteNumbers = new Array(byteCharacters.length)
      .fill(0)
      .map((_, i) => byteCharacters.charCodeAt(i));
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: contentType });
  };

  private readonly serialize = async (blob: Blob) => {
    const base64Data = await this.blobToBase64(blob);
    return base64Data;
  };

  private readonly deserialize = (text: string): Blob => {
    return this.base64ToBlob(text);
  };

  public readonly load = async (
    for_date: DateTime,
    run_type: RunType,
    run_date: DateTime,
    filename: string
  ) => {
    await this.downloadAndStorePMTiles(for_date, run_type, run_date, filename);
    const file = await this.fileSystem.readFile({
      path: filename,
      directory: Directory.Data,
      encoding: Encoding.UTF8,
    });

    const deserialized = this.deserialize(file.data as string);

    // Initialize PMTiles with local blob
    const pmtiles = new PMTiles(
      new FileSource(new File([deserialized], filename))
    );
    return pmtiles;
  };
}
