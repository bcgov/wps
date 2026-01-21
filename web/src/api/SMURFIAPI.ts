import axios from "@/api/axios"
import { SpotAdminRowResponse } from "@/features/smurfi/interfaces"

export async function getSpotAdminRows(): Promise<SpotAdminRowResponse> {
    const url = '/smurfi/admin/'
    const { data } = await axios.get(url)
    return data
}