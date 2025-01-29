import { RunType } from "@/api/fbaAPI";
import { PMTILES_BUCKET } from "@/utils/env";
import { DateTime } from "luxon";

/**
 *
 * @param for_date The date of the hfi to process. (when is the hfi for?)
 * @param run_type forecast or actual
 * @param run_date The date of the run to process. (when was the hfi file created?)
 * @returns pmtiles blob
 */
export const fetchPMTiles = async (
  for_date: DateTime,
  run_type: RunType,
  run_date: DateTime
): Promise<Blob> => {
  const PMTilesURL = `${PMTILES_BUCKET}hfi/${run_type.toLowerCase()}/${run_date.toISODate()}/hfi${for_date.toISODate(
    {
      format: "basic",
    }
  )}.pmtiles`;

  const response = await fetch(PMTilesURL);
  const blob = await response.blob();

  return blob;
};
