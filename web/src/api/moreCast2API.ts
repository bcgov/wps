import axios from 'api/axios'
import { BiasAdjModelResponse, ModelsForStation } from 'api/modelAPI'
import { Station } from 'api/stationAPI'

export enum ModelChoice {
  GDPS = 'GDPS',
  GFS = 'GFS',
  HRDPS = 'HRDPS',
  NAMM = 'NAMM',
  RDPS = 'RDPS',
  MANUAL = 'MANUAL'
}

interface PredictionValues {
  precip: number
  rh: number
  temp: number
  wind_direction: number
  wind_speed: number
}

export interface StationPrediction {
  date: number
  model: ModelChoice
  station: Station
  values: PredictionValues
}

export interface ModelPredictionResponse {
  predictions: StationPrediction[]
}

export type ModelType = 'HRDPS' | 'GDPS' | 'GFS' | 'MANUAL' | 'NAMM' | 'RDPS'

export const ModelChoices: ModelType[] = [
  ModelChoice.GDPS,
  ModelChoice.GFS,
  ModelChoice.HRDPS,
  ModelChoice.MANUAL,
  ModelChoice.NAMM,
  ModelChoice.RDPS
]

/**
 * Get noon model predictions for the specified date range
 * @param stationCodes A list of station codes of interest
 * @param model The weather model abbreviation
 * @param from_date The first date (epoch time) for which predictions will be returned
 * @param to_date The last date (epoch time) for which predictions will be returned
 */
// TODO - Uncomment once we're wired up to the API
// export async function getModelPredictionsWIP(
//   stationCodes: number[],
//   model: ModelType,
//   startDate: number,
//   endDate: number
// ): Promise<ModelsForStation[]> {
//   const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
//   const { data } = await axios.post<BiasAdjModelResponse>(url, {
//     stations: stationCodes
//   })

//   return data.stations
// }

// TODO - To be removed once we're wired up to the API
export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  startDate: number,
  endDate: number
): Promise<ModelsForStation[]> {
  try {
    const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
    await axios.post<BiasAdjModelResponse>(url, {
      stations: stationCodes
    })
  } catch {
    console.log('Not expecting the API to work yet.')
  }

  if (model === ModelChoice.HRDPS) {
    return completeSampleData.stations
  } else {
    return []
  }
}

const completeSampleData = {
  stations: [
    {
      station: {
        zone_code: null,
        code: 838,
        name: 'AKOKLI CREEK',
        lat: 49.4358,
        long: -116.7464,
        ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 15,
          end_month: 8,
          end_day: 31
        },
        elevation: 821,
        wfwx_station_uuid: ''
      },
      model_runs: [
        {
          model_run: {
            datetime: '2023-02-16T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T08:00:00+00:00',
              temperature: -5.962998789274375,
              bias_adjusted_temperature: null,
              relative_humidity: 65.45828423679694,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4438747763633728,
              wind_direction: 135.3990936279297,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T09:00:00+00:00',
              temperature: -6.097130320623354,
              bias_adjusted_temperature: null,
              relative_humidity: 65.48142757353017,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.44963937997817993,
              wind_direction: 138.53504943847656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T10:00:00+00:00',
              temperature: -6.263019254835273,
              bias_adjusted_temperature: null,
              relative_humidity: 65.21814622971182,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5130500793457031,
              wind_direction: 139.365162,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T11:00:00+00:00',
              temperature: -6.428006046691311,
              bias_adjusted_temperature: null,
              relative_humidity: 63.50330099774418,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5245792865753174,
              wind_direction: 135.4913330078125,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T12:00:00+00:00',
              temperature: -6.8268542815974325,
              bias_adjusted_temperature: null,
              relative_humidity: 70.64289325779427,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4899916350841522,
              wind_direction: 357.8668212890625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T13:00:00+00:00',
              temperature: -6.7484912964477655,
              bias_adjusted_temperature: null,
              relative_humidity: 68.24756108065844,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5476377010345459,
              wind_direction: 135.1223907470703,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T14:00:00+00:00',
              temperature: -6.793122979434628,
              bias_adjusted_temperature: null,
              relative_humidity: 70.06735324990572,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5879899263381958,
              wind_direction: 133.7388916015625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T15:00:00+00:00',
              temperature: -6.893840923203946,
              bias_adjusted_temperature: null,
              relative_humidity: 74.940368986377,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6456360220909119,
              wind_direction: 136.5059051513672,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T16:00:00+00:00',
              temperature: -6.392061303009676,
              bias_adjusted_temperature: null,
              relative_humidity: 77.76659021529869,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6686944365501404,
              wind_direction: 137.52047729492188,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T17:00:00+00:00',
              temperature: -3.7782895035943493,
              bias_adjusted_temperature: null,
              relative_humidity: 70.67962796916802,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5937545299530029,
              wind_direction: 151.72447204589844,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-16T18:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-16T18:00:00+00:00',
              temperature: -2.5437994711083776,
              bias_adjusted_temperature: null,
              relative_humidity: 65.46317548753133,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5879899263381958,
              wind_direction: 229.7541961669922,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T19:00:00+00:00',
              temperature: -0.7203167332820102,
              bias_adjusted_temperature: null,
              relative_humidity: 64.58772828457755,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6975175142288208,
              wind_direction: 202.08407592773438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T20:00:00+00:00',
              temperature: 0.2607399155343037,
              bias_adjusted_temperature: null,
              relative_humidity: 63.78617477416992,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7609281539916992,
              wind_direction: 205.4044952392578,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T21:00:00+00:00',
              temperature: 0.9012085430866299,
              bias_adjusted_temperature: null,
              relative_humidity: 60.63288247444052,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7609281539916992,
              wind_direction: 198.48695373535156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T22:00:00+00:00',
              temperature: 1.1564119619807522,
              bias_adjusted_temperature: null,
              relative_humidity: 58.62138061057412,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7148113250732422,
              wind_direction: 189.6325225830078,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-16T23:00:00+00:00',
              temperature: 1.2327678705373835,
              bias_adjusted_temperature: null,
              relative_humidity: 56.06494221443628,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.7321051359176636,
              wind_direction: 168.87994384765625,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T00:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T00:00:00+00:00',
              temperature: 0.6783769975226465,
              bias_adjusted_temperature: 0.8,
              relative_humidity: 46.878147744057145,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.8128096461296082,
              wind_direction: 301.8809509277344,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T01:00:00+00:00',
              temperature: -0.6844901347694756,
              bias_adjusted_temperature: null,
              relative_humidity: 58.699670316337894,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6225776076316833,
              wind_direction: 131.3408203125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T02:00:00+00:00',
              temperature: -1.4855321688493106,
              bias_adjusted_temperature: null,
              relative_humidity: 62.38987086250255,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.6341068148612976,
              wind_direction: 134.29229736328125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T03:00:00+00:00',
              temperature: -1.7161624911509699,
              bias_adjusted_temperature: null,
              relative_humidity: 64.2679941960202,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.5188146829605103,
              wind_direction: 134.7534637451172,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T04:00:00+00:00',
              temperature: -1.7750412405763552,
              bias_adjusted_temperature: null,
              relative_humidity: 65.92045339029522,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 132.26315307617188,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T05:00:00+00:00',
              temperature: -1.7790834443858694,
              bias_adjusted_temperature: null,
              relative_humidity: 65.75520663970909,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.49575623869895935,
              wind_direction: 131.52528381347656,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T06:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T06:00:00+00:00',
              temperature: -0.5874637251146917,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 62.34931417086173,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 1.1644506454467773,
              wind_direction: 258.16217041015625,
              delta_precipitation: 0.0007205759175121784
            },
            {
              datetime: '2023-02-17T07:00:00+00:00',
              temperature: -1.8418562322402834,
              bias_adjusted_temperature: null,
              relative_humidity: 66.53921085113487,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 134.10781562,
              delta_precipitation: 0.0006571409584364616
            },
            {
              datetime: '2023-02-17T08:00:00+00:00',
              temperature: -1.8284405653782203,
              bias_adjusted_temperature: null,
              relative_humidity: 66.41300974336886,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 131.8942108154297,
              delta_precipitation: 0.0003602879587560892
            },
            {
              datetime: '2023-02-17T09:00:00+00:00',
              temperature: -2.027996838225413,
              bias_adjusted_temperature: null,
              relative_humidity: 67.98264809234317,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.3574056625366211,
              wind_direction: 128.4815673828125,
              delta_precipitation: 0.0001167513970196331
            },
            {
              datetime: '2023-02-17T10:00:00+00:00',
              temperature: -2.2275654132426963,
              bias_adjusted_temperature: null,
              relative_humidity: 67.71248197823955,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.253642737865448,
              wind_direction: 121.10287475585938,
              delta_precipitation: 0.00018010160266073924
            },
            {
              datetime: '2023-02-17T11:00:00+00:00',
              temperature: -2.2260746958480553,
              bias_adjusted_temperature: null,
              relative_humidity: 68.60133711061701,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.253642737865448,
              wind_direction: 129.820312,
              delta_precipitation: 0.0
            }
          ]
        },
        {
          model_run: {
            datetime: '2023-02-17T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T12:00:00+00:00',
              temperature: -1.2703204323223796,
              bias_adjusted_temperature: -0.2,
              relative_humidity: 66.01870695027247,
              bias_adjusted_relative_humidity: 74.0,
              wind_speed: 1.614090085029602,
              wind_direction: 308.3373107910156,
              delta_precipitation: 0.001781117998082234
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -2.3350042896413123,
              bias_adjusted_temperature: null,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.14987978339195251,
              wind_direction: 147.6661834716797,
              delta_precipitation: 0.001309222656307023
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -2.4237188892506873,
              bias_adjusted_temperature: null,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.06917528808116913,
              wind_direction: 99.3357162475586,
              delta_precipitation: 0.0011924712592873896
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -2.5499439731570037,
              bias_adjusted_temperature: null,
              relative_humidity: 71.92166295873494,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.09223371744155884,
              wind_direction: 42.611976623535156,
              delta_precipitation: 0.0005937059993607447
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -2.4082986690135093,
              bias_adjusted_temperature: null,
              relative_humidity: 72.78944693366184,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.19599664211273193,
              wind_direction: 51.835350036621094,
              delta_precipitation: 0.000593706191197506
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -1.287573403209333,
              bias_adjusted_temperature: null,
              relative_humidity: 69.18156453068302,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.2305842936038971,
              wind_direction: 25.27203941345215,
              delta_precipitation: 0.0011874119987214894
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: 0.4839150567417877,
              bias_adjusted_temperature: null,
              relative_humidity: 62.293685558180044,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.26517194509506226,
              wind_direction: 355.37652587890625,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: 1.2502212617482775,
              bias_adjusted_temperature: null,
              relative_humidity: 60.420817093501526,
              bias_adjusted_relative_humidity: null,
              wind_speed: 0.4611685872077942,
              wind_direction: 311.8421936035156,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: 1.33592342873342,
              bias_adjusted_temperature: 0.7,
              relative_humidity: 60.897190360824936,
              bias_adjusted_relative_humidity: 68.0,
              wind_speed: 0.4611685872077942,
              wind_direction: 248.47763061523438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: 1.2533243114387682,
              bias_adjusted_temperature: 2.3,
              relative_humidity: 60.812347157067514,
              bias_adjusted_relative_humidity: 59.0,
              wind_speed: 0.7378697395324707,
              wind_direction: 196.08888244628906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: 1.4960745287112789,
              bias_adjusted_temperature: 1.6,
              relative_humidity: 57.43936241013993,
              bias_adjusted_relative_humidity: 63.0,
              wind_speed: 0.9915124773979187,
              wind_direction: 183.6373291015625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: 1.491539208427355,
              bias_adjusted_temperature: 2.0,
              relative_humidity: 55.75096457412904,
              bias_adjusted_relative_humidity: 61.0,
              wind_speed: 1.1875090599060059,
              wind_direction: 187.41891479492188,
              delta_precipitation: 0.0007205761093489384
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: 1.0736929340052979,
              bias_adjusted_temperature: 0.8,
              relative_humidity: 55.813537003469996,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.9569247961044312,
              wind_direction: 192.58399963378906,
              delta_precipitation: -0.0008474458356636117
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: 0.2896222507433703,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 59.50250945644533,
              bias_adjusted_relative_humidity: 70.0,
              wind_speed: 0.7609281539916992,
              wind_direction: 184.83636474609375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -0.38186905707445984,
              bias_adjusted_temperature: -0.7,
              relative_humidity: 62.62098002984679,
              bias_adjusted_relative_humidity: 71.0,
              wind_speed: 0.5764607191085815,
              wind_direction: 179.57904052734375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -0.7486534299838582,
              bias_adjusted_temperature: -0.1,
              relative_humidity: 64.3009031800602,
              bias_adjusted_relative_humidity: 65.0,
              wind_speed: 0.553402304649353,
              wind_direction: 180.77809143066406,
              delta_precipitation: 0.00048724263034213323
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -1.0739074534190811,
              bias_adjusted_temperature: -0.1,
              relative_humidity: 68.2821469852489,
              bias_adjusted_relative_humidity: 69.0,
              wind_speed: 0.749398946762085,
              wind_direction: 166.11293029785156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -1.4131158947399338,
              bias_adjusted_temperature: 0.0,
              relative_humidity: 71.77719726909814,
              bias_adjusted_relative_humidity: 68.0,
              wind_speed: 0.8646910786628723,
              wind_direction: 155.13851562,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -1.6877098544356826,
              bias_adjusted_temperature: -0.3,
              relative_humidity: 75.13296943397938,
              bias_adjusted_relative_humidity: 67.0,
              wind_speed: 0.807045042514801,
              wind_direction: 150.8320312,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -1.9007479347008753,
              bias_adjusted_temperature: -0.5,
              relative_humidity: 76.97755894631018,
              bias_adjusted_relative_humidity: 73.0,
              wind_speed: 0.8531618714332581,
              wind_direction: 147.20501708984375,
              delta_precipitation: 0.0
            }
          ]
        }
      ]
    }
  ]
}
