import {
  FireShapeStatusDetail,
  FireZoneHFIStatsDictionary,
  FireZoneTPIStats,
  getHFIStats,
  getProvincialSummary,
  getTPIStats,
  RunParameter,
} from "@/api/fbaAPI";
import { PST_UTC_OFFSET } from "@/utils/constants";
import { CacheableData, CacheableDataType } from "@/utils/storage";
import { isEqual, isNil } from "lodash";
import { DateTime } from "luxon";

export const today = DateTime.now().setZone(`UTC${PST_UTC_OFFSET}`);
export const getTodayKey = () => {
  return today.isValid ? today.toISODate() : "";
};
export const getTomorrowKey = () => {
  return today.isValid ? today.plus({ days: 1 }).toISODate() : "";
};

export const runParametersMatch = (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter },
  data: CacheableData<CacheableDataType>
): boolean => {
  return (
    isEqual(runParameters[todayKey], data[todayKey]?.runParameter) &&
    isEqual(runParameters[tomorrowKey], data[tomorrowKey]?.runParameter)
  );
};

export const fetchHFIStatsForRunParameter = async (
  runParameter: RunParameter
): Promise<FireZoneHFIStatsDictionary> => {
  if (isNil(runParameter)) {
    return [];
  }
  const hfiStatsForRunParameter = await getHFIStats(
    runParameter.run_type,
    runParameter.run_datetime,
    runParameter.for_date
  );
  return hfiStatsForRunParameter?.zone_data;
};

export const fetchHFIStats = async (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter }
): Promise<CacheableData<FireZoneHFIStatsDictionary>> => {
  const hfiStatsForToday = await fetchHFIStatsForRunParameter(
    runParameters[todayKey]
  );
  const hfiStatsForTommorow = await fetchHFIStatsForRunParameter(
    runParameters[tomorrowKey]
  );
  const hfiStats = shapeDataForCaching(
    todayKey,
    tomorrowKey,
    runParameters,
    hfiStatsForToday,
    hfiStatsForTommorow
  );
  return hfiStats as CacheableData<FireZoneHFIStatsDictionary>;
};

export const fetchTpiStatsForRunParameter = async (
  runParameter: RunParameter
): Promise<FireZoneTPIStats[]> => {
  if (isNil(runParameter)) {
    return [];
  }
  const tpiStatsForRunParameter = await getTPIStats(
    runParameter.run_type,
    runParameter.run_datetime,
    runParameter.for_date
  );
  return tpiStatsForRunParameter?.firezone_tpi_stats;
};

export const fetchTpiStats = async (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter }
): Promise<CacheableData<FireZoneTPIStats[]>> => {
  const tpiStatsForToday = await fetchTpiStatsForRunParameter(
    runParameters[todayKey]
  );
  const tpiStatsForTommorow = await fetchTpiStatsForRunParameter(
    runParameters[tomorrowKey]
  );
  const tpiStats = shapeDataForCaching(
    todayKey,
    tomorrowKey,
    runParameters,
    tpiStatsForToday,
    tpiStatsForTommorow
  );
  return tpiStats as CacheableData<FireZoneTPIStats[]>;
};

export const fetchProvincialSummary = async (
  runParameter: RunParameter
): Promise<FireShapeStatusDetail[]> => {
  if (isNil(runParameter)) {
    return [];
  }
  const provincialSummary = await getProvincialSummary(
    runParameter.run_type,
    runParameter.run_datetime,
    runParameter.for_date
  );
  return provincialSummary?.provincial_summary;
};

export const fetchProvincialSummaries = async (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter }
): Promise<CacheableData<FireShapeStatusDetail[]>> => {
  // API calls to get data for today and tomorrow
  const todayProvincialSummary = await fetchProvincialSummary(
    runParameters[todayKey]
  );
  const tomorrowProvincialSummary = await fetchProvincialSummary(
    runParameters[tomorrowKey]
  );
  // Shape the data for caching and storing in state
  const provincialSummaries = {
    [todayKey]: {
      runParameter: runParameters[todayKey],
      data: todayProvincialSummary,
    },
    [tomorrowKey]: {
      runParameter: runParameters[tomorrowKey],
      data: tomorrowProvincialSummary,
    },
  };

  return provincialSummaries;
};

export const shapeDataForCaching = (
  todayKey: string,
  tomorrowKey: string,
  runParameters: { [key: string]: RunParameter },
  todayData: CacheableDataType,
  tomorrowData: CacheableDataType
): CacheableData<CacheableDataType> => {
  return {
    [todayKey]: {
      runParameter: runParameters[todayKey],
      data: todayData,
    },
    [tomorrowKey]: {
      runParameter: runParameters[tomorrowKey],
      data: tomorrowData,
    },
  };
};

export const dataAreEqual = (
  a: CacheableData<CacheableDataType> | null,
  b: CacheableData<CacheableDataType> | null
): boolean => {
  return isEqual(a, b);
};
