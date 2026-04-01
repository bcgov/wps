import axios from "api/axios";
import type { FireCentre } from "@wps/types/fireCentre";

export interface FireCentresResponse {
  fire_centres: FireCentre[];
}

export async function getFireCentres(): Promise<FireCentresResponse> {
  const url = "psu/fire-centres";
  const { data } = await axios.get(url);
  return data;
}
