import axios from 'api/axios'
import { isNil } from "lodash"
import { DateTime } from "luxon"

export enum ModelSkillEnum {
    GDPS = 'GDPS',
    RDPS = 'RDPS',
    HRDPS = 'HRDPS',
    GFS = 'GFS',
    NAM = 'NAM'
}

export enum WeatherParamEnum {
    PRECIP = "precip",
    RH = "rh",
    TEMP = "temp",
    WIND_DIR = "wind_dir",
    WIND_SPEED = "wind_speed"
}

export interface ModelSkillStats {
    max: number,
    mean: number,
    min: number,
    rmse: number,
    model: ModelSkillEnum
    percentile25: number,
    percentile75: number,
    raw: number[]
}

export interface RankedModelSkillStats extends ModelSkillStats{
  rank: number
}

export interface ModelSkillSummaryData {
  data: number[]
  model: string
  rmse: number
}

export interface RankedModelSkillSummaryData extends ModelSkillSummaryData{
  rank: number
}

interface DaySkillStats {
    day: number
    modelSkillStats: ModelSkillStats[]
}

export interface WeatherParamSkillStats {
    weatherParam: WeatherParamEnum
    daySkillStats: DaySkillStats[]
}

export interface SkillStatsResponse {
    skillStats: WeatherParamSkillStats[]
}

export async function fetchSkillStats(
  startDate: DateTime,
  days: number,
  stationCodes: number[]
): Promise<SkillStatsResponse> {
  if (stationCodes.length === 0) {
    return {
      skillStats: []
    }
  }
  const url = `/skill/score/${startDate.toISODate()}/${days}`
  const { data } = await axios.post<SkillStatsResponse>(url, {
    stations: stationCodes  })
  return data
}

export interface StationSkillData {
  stationCode: number
  skillData: number[]
}

export interface ModelSkillData {
  model: ModelSkillEnum
  stationSkillData: StationSkillData[]
}

export interface DaySkillData {
  day: number
  modelSkillData: ModelSkillData[]
}

export interface WeatherParamSkillData {
  weatherParam: WeatherParamEnum
  daySkillData: DaySkillData[]
}

export interface SkillDataResponse {
  skillData: WeatherParamSkillData[]
}

export async function fetchSkillStats2(
  startDate: DateTime,
  days: number,
  stationCodes: number[]
): Promise<SkillDataResponse> {
  if (stationCodes.length === 0) {
    return {
      skillData: []
    }
  }
  const url = `/skill/score2/${startDate.toISODate()}/${days}`
  const { data } = await axios.post<SkillDataResponse>(url, {
    stations: stationCodes  })
  return data
}