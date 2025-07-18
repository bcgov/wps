import axios from "api/axios";

export enum RunType {
  FORECAST = "FORECAST",
  ACTUAL = "ACTUAL",
}

export interface FireCenterStation {
  code: number;
  name: string;
  zone?: string;
}

export interface FireCenter {
  id: number;
  name: string;
  stations: FireCenterStation[];
}

export interface FireShape {
  fire_shape_id: number;
  mof_fire_zone_name: string;
  mof_fire_centre_name: string;
  area_sqm?: number;
}

export interface FBAResponse {
  fire_centers: FireCenter[];
}

export interface AdvisoryCriticalHours {
  start_time?: number;
  end_time?: number;
}

export interface AdvisoryMinWindStats {
  threshold: HfiThreshold
  min_wind_speed?: number
}

export interface FireZoneFuelStats {
  fuel_type: FuelType;
  threshold: HfiThreshold;
  critical_hours: AdvisoryCriticalHours;
  area: number;
  fuel_area: number;
}

export interface FireShapeArea {
  fire_shape_id: number;
  threshold?: number;
  combustible_area: number;
  elevated_hfi_area?: number;
  elevated_hfi_percentage: number;
}

export interface ElevationInfo {
  minimum: number;
  quartile_25: number;
  median: number;
  quartile_75: number;
  maximum: number;
}

export interface ElevationInfoByThreshold {
  threshold: number;
  elevation_info: ElevationInfo;
}

export interface FireZoneElevationInfoResponse {
  hfi_elevation_info: ElevationInfoByThreshold[];
}

export interface FireZoneTPIStats {
  fire_zone_id: number;
  valley_bottom_hfi?: number;
  valley_bottom_tpi?: number;
  mid_slope_hfi?: number;
  mid_slope_tpi?: number;
  upper_slope_hfi?: number;
  upper_slope_tpi?: number;
}

export interface FireCentreTPIResponse {
  fire_centre_name: string
  firezone_tpi_stats: FireZoneTPIStats[]
}

export interface FireShapeAreaListResponse {
  shapes: FireShapeArea[];
}

// Fire shape area (aka fire zone unit) data transfer object
export interface FireShapeAreaDetail extends FireShapeArea {
  fire_shape_name: string;
  fire_centre_name: string;
}

// Response object for provincial summary request
export interface ProvincialSummaryResponse {
  provincial_summary: FireShapeAreaDetail[];
}

export interface HfiThresholdFuelTypeArea {
  fuel_type_id: number;
  threshold_id: number;
  area: number;
}

export interface HfiThreshold {
  id: number;
  name: string;
  description: string;
}

export interface FireZoneHFIStats {
  min_wind_stats: AdvisoryMinWindStats[]
  fuel_area_stats: FireZoneFuelStats[]
}

export interface FuelType {
  fuel_type_id: number;
  fuel_type_code: string;
  description: string;
}

export interface FireCentreHFIStats {
  [fire_centre_name: string]: {
    [fire_zone_id: number]: FireZoneHFIStats;
  };
}

export interface RunParameter {
  for_date: string
  run_datetime: string
  run_type: RunType
}

const ASA_GO_API_PREFIX = "asa-go"

export async function getFBAFireCenters(): Promise<FBAResponse> {
  const url = `${ASA_GO_API_PREFIX}/fire-centers`;

  const { data } = await axios.get(url);
  return data;
}

export async function getFireShapeAreas(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireShapeAreaListResponse> {
  const url = `${ASA_GO_API_PREFIX}/fire-shape-areas/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`;
  const { data } = await axios.get(url);
  return data;
}

// Gets a summary of info about all fire zone units in the province
export async function getProvincialSummary(
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<ProvincialSummaryResponse> {
  const url = `${ASA_GO_API_PREFIX}/provincial-summary/${run_type.toLowerCase()}/${encodeURI(run_datetime)}/${for_date}`;
  const { data } = await axios.get(url);
  return data;
}

export async function getMostRecentRunParameter(forDate: string): Promise<RunParameter> {
  const url = `${ASA_GO_API_PREFIX}/latest-sfms-run-datetime/${forDate}`;
  const { data } = await axios.get(url);
  return data.run_parameter;
}

export async function getFireCentreHFIStats(
  run_type: RunType,
  for_date: string,
  run_datetime: string,
  fire_centre: string
): Promise<FireCentreHFIStats> {
  const url = `${ASA_GO_API_PREFIX}/fire-centre-hfi-stats/${run_type.toLowerCase()}/${for_date}/${run_datetime}/${fire_centre}`;
  const { data } = await axios.get(url);
  return data;
}

export async function getFireZoneElevationInfo(
  fire_zone_id: number,
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireZoneElevationInfoResponse> {
  const url = `${ASA_GO_API_PREFIX}/fire-zone-elevation-info/${run_type.toLowerCase()}/${run_datetime}/${for_date}/${fire_zone_id}`;
  const { data } = await axios.get(url);
  return data;
}

export async function getFireCentreTPIStats(
  fire_centre_name: string,
  run_type: RunType,
  run_datetime: string,
  for_date: string
): Promise<FireCentreTPIResponse> {
  const url = `${ASA_GO_API_PREFIX}/fire-centre-tpi-stats/${run_type.toLowerCase()}/${run_datetime}/${for_date}/${fire_centre_name}`;
  const { data } = await axios.get(url);
  return data;
}