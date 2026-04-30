import axios from "api/axios";
import type { FireCentre } from "@/types/fireCentre";

export interface FireCentresResponse {
  fire_centres: FireCentre[];
}

export async function getFireCentres(): Promise<FireCentresResponse> {
  const url = "asa-go/fire-centres";
  const { data } = await axios.get(url);
  return data;
}
