import axios from 'api/axios'

export interface ModelRun {
  model_run_timestamp: string
  prediction_timestamps: string[]
}

export interface ModelRuns {
  model_runs: ModelRun[]
}

export async function getModelRuns(): Promise<ModelRuns> {
  const url = '/c-haines/model-runs/'
  const { data } = await axios.get(url)
  return data
}
