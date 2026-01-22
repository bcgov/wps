import axios from '@/api/axios'
import { FetchChefsFormResponse, SpotAdminRowResponse } from '@/features/smurfi/interfaces'

export async function getSpotAdminRows(): Promise<SpotAdminRowResponse> {
  const url = '/smurfi/admin/'
  const { data } = await axios.get(url)
  return data
}

export async function runFetchChefsForms(): Promise<FetchChefsFormResponse> {
  const url = 'smurfi/pull_from_chefs'
  const { data } = await axios.get(url)
  return data
}
