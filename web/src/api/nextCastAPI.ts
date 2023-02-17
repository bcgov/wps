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
export async function getModelPredictionsWIP(
  stationCodes: number[],
  model: ModelType,
  startDate: number,
  endDate: number
): Promise<ModelsForStation[]> {
  const url = `/weather_models/${model}/predictions/most_recent/${startDate}/${endDate}`
  const { data } = await axios.post<BiasAdjModelResponse>(url, {
    stations: stationCodes
  })

  return data.stations
}

export async function getModelPredictions(
  stationCodes: number[],
  model: ModelType,
  startDate: number,
  endDate: number
): Promise<ModelsForStation[]> {
  return sampleAPIData.stations
}

const sampleAPIData = {
  stations: [
    {
      station: {
        zone_code: null,
        code: 209,
        name: 'ALEXIS CREEK',
        lat: 52.08377,
        long: -123.2732667,
        ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
        core_season: {
          start_month: 5,
          start_day: 15,
          end_month: 8,
          end_day: 31
        },
        elevation: 791,
        wfwx_station_uuid: ''
      },
      model_runs: [
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
              temperature: -12.312169521388572,
              bias_adjusted_temperature: -13.233632635690624,
              relative_humidity: 86.77078519853998,
              bias_adjusted_relative_humidity: 72.58798416654975,
              wind_speed: 0.11529214680194855,
              wind_direction: 31.636165618896484,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -11.849701676410728,
              bias_adjusted_temperature: -12.626476945471886,
              relative_humidity: 83.0155489798751,
              bias_adjusted_relative_humidity: 77.13813663343717,
              wind_speed: 0.29975956678390503,
              wind_direction: 315.53155517578125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -12.11997044944774,
              bias_adjusted_temperature: -13.069478426950102,
              relative_humidity: 82.2117907791166,
              bias_adjusted_relative_humidity: 77.12368450299023,
              wind_speed: 0.14987978339195251,
              wind_direction: 295.8857727050781,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -12.584600576400867,
              bias_adjusted_temperature: -13.594342027112429,
              relative_humidity: 83.0155489798751,
              bias_adjusted_relative_humidity: 78.47394268865683,
              wind_speed: 0.08070450276136398,
              wind_direction: 306.4926452636719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -12.655759924702384,
              bias_adjusted_temperature: -13.659295946527731,
              relative_humidity: 84.97619875377865,
              bias_adjusted_relative_humidity: 77.57925987549486,
              wind_speed: 0.13835057616233826,
              wind_direction: 340.6191101074219,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -11.299680060257,
              bias_adjusted_temperature: -11.420699545889725,
              relative_humidity: 89.62353515625,
              bias_adjusted_relative_humidity: 78.16454065427752,
              wind_speed: 0.06917528808116913,
              wind_direction: 60.4130859375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: -8.25021584905584,
              bias_adjusted_temperature: -8.419331110874268,
              relative_humidity: 86.82263551372455,
              bias_adjusted_relative_humidity: 76.82077392287808,
              wind_speed: 0.20752586424350739,
              wind_direction: 21.58268928527832,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: -6.136180900433602,
              bias_adjusted_temperature: -6.307809973471964,
              relative_humidity: 76.34392438062636,
              bias_adjusted_relative_humidity: 69.65689300216181,
              wind_speed: 0.034587644040584564,
              wind_direction: 60.966487884521484,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: -4.52872583733904,
              bias_adjusted_temperature: -4.312225279261454,
              relative_humidity: 68.08540997632949,
              bias_adjusted_relative_humidity: 60.39093168467702,
              wind_speed: 0.10376293212175369,
              wind_direction: 91.86478424072266,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: -3.1589823689488323,
              bias_adjusted_temperature: -3.4304050573997587,
              relative_humidity: 63.223337105006806,
              bias_adjusted_relative_humidity: 58.45952420723604,
              wind_speed: 0.253642737865448,
              wind_direction: 92.51042175292969,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: -1.6782782976959063,
              bias_adjusted_temperature: -2.1675297126434905,
              relative_humidity: 56.71444837681535,
              bias_adjusted_relative_humidity: 59.75377046321892,
              wind_speed: 0.17293822765350342,
              wind_direction: 80.70450592041016,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: -1.2202677678843024,
              bias_adjusted_temperature: -0.6684814941828281,
              relative_humidity: 54.17564084964684,
              bias_adjusted_relative_humidity: 54.248104965844846,
              wind_speed: 0.2305842936038971,
              wind_direction: 52.48098373413086,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: -1.4874670726124992,
              bias_adjusted_temperature: -1.1663812365715562,
              relative_humidity: 57.0347751717169,
              bias_adjusted_relative_humidity: 50.37323043665444,
              wind_speed: 0.3804640769958496,
              wind_direction: 89.65117645263672,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: -2.2131295070937114,
              bias_adjusted_temperature: -0.9701497489450448,
              relative_humidity: 62.21060145463842,
              bias_adjusted_relative_humidity: 50.67152889622081,
              wind_speed: 0.2767011523246765,
              wind_direction: 200.7928009033203,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -3.1505710066128874,
              bias_adjusted_temperature: -1.1786717576210806,
              relative_humidity: 68.44760206180504,
              bias_adjusted_relative_humidity: 56.13175476051069,
              wind_speed: 0.5879899263381958,
              wind_direction: 255.5796356201172,
              delta_precipitation: 0.005581922577392508
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -4.203843383380217,
              bias_adjusted_temperature: -2.064708552872678,
              relative_humidity: 95.42117309570312,
              bias_adjusted_relative_humidity: 90.05182617006486,
              wind_speed: 0.7839865684509277,
              wind_direction: 117.41352081298828,
              delta_precipitation: 0.8663007895206221
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -4.2211164683126565,
              bias_adjusted_temperature: -2.0815766030760714,
              relative_humidity: 95.80660063913382,
              bias_adjusted_relative_humidity: 91.04334490233681,
              wind_speed: 1.2797428369522095,
              wind_direction: 135.58355712890625,
              delta_precipitation: 1.20289979506932
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -4.035143944422762,
              bias_adjusted_temperature: -1.561236635468465,
              relative_humidity: 94.91081237792969,
              bias_adjusted_relative_humidity: 86.371924150683,
              wind_speed: 1.152921438217163,
              wind_direction: 112.52513885498047,
              delta_precipitation: 0.38705701132000847
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -3.8749140499322094,
              bias_adjusted_temperature: -1.7881704434515102,
              relative_humidity: 94.44732666015625,
              bias_adjusted_relative_humidity: 94.40095802079335,
              wind_speed: 0.8877495527267456,
              wind_direction: 134.84568786621094,
              delta_precipitation: 0.024093108847107025
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -4.231070602451891,
              bias_adjusted_temperature: -1.616856688635448,
              relative_humidity: 93.47750416313042,
              bias_adjusted_relative_humidity: 84.2530747894207,
              wind_speed: 0.47269779443740845,
              wind_direction: 181.79266357421875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T08:00:00+00:00',
              temperature: -4.583852406120542,
              bias_adjusted_temperature: -2.426749750335212,
              relative_humidity: 94.44732666015625,
              bias_adjusted_relative_humidity: 85.44645010897503,
              wind_speed: 0.44963937997817993,
              wind_direction: 274.1186218261719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T09:00:00+00:00',
              temperature: -4.678225367017346,
              bias_adjusted_temperature: -2.6933045354031924,
              relative_humidity: 91.495849609375,
              bias_adjusted_relative_humidity: 82.59538049810158,
              wind_speed: 0.553402304649353,
              wind_direction: 284.3565368652344,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T10:00:00+00:00',
              temperature: -4.710904766614844,
              bias_adjusted_temperature: -2.9844994574066073,
              relative_humidity: 88.54437255859375,
              bias_adjusted_relative_humidity: 80.19637481434066,
              wind_speed: 0.7378697395324707,
              wind_direction: 285.6478271484375,
              delta_precipitation: 0.0022056170293529576
            },
            {
              datetime: '2023-02-18T11:00:00+00:00',
              temperature: -4.756337757683043,
              bias_adjusted_temperature: -3.368173647188269,
              relative_humidity: 86.88155732768939,
              bias_adjusted_relative_humidity: 79.3631721562171,
              wind_speed: 0.8762203454971313,
              wind_direction: 276.33221435546875,
              delta_precipitation: 0.033829013607844516
            },
            {
              datetime: '2023-02-18T12:00:00+00:00',
              temperature: -4.753722048831968,
              bias_adjusted_temperature: -4.0371542960075955,
              relative_humidity: 88.84221376386236,
              bias_adjusted_relative_humidity: 72.44090858579838,
              wind_speed: 1.262449026107788,
              wind_direction: 298.7450256347656,
              delta_precipitation: 0.12406596407366877
            },
            {
              datetime: '2023-02-18T13:00:00+00:00',
              temperature: -4.6636237581354365,
              bias_adjusted_temperature: -3.4973374354027964,
              relative_humidity: 94.44732666015625,
              bias_adjusted_relative_humidity: 80.78509251035567,
              wind_speed: 1.3835058212280273,
              wind_direction: 293.85662841796875,
              delta_precipitation: 0.5933391504316639
            },
            {
              datetime: '2023-02-18T14:00:00+00:00',
              temperature: -4.5965576106432415,
              bias_adjusted_temperature: -3.891369936241068,
              relative_humidity: 94.44732666015625,
              bias_adjusted_relative_humidity: 79.29842159158541,
              wind_speed: 1.1413922309875488,
              wind_direction: 285.832275390625,
              delta_precipitation: 0.20685591713611373
            },
            {
              datetime: '2023-02-18T15:00:00+00:00',
              temperature: -4.83644783067024,
              bias_adjusted_temperature: -4.482413026234369,
              relative_humidity: 92.46567210640083,
              bias_adjusted_relative_humidity: 81.17452284518728,
              wind_speed: 1.2220968008041382,
              wind_direction: 274.3952941894531,
              delta_precipitation: 0.003978604310027389
            },
            {
              datetime: '2023-02-18T16:00:00+00:00',
              temperature: -5.086413778181235,
              bias_adjusted_temperature: -4.668051599237179,
              relative_humidity: 91.495849609375,
              bias_adjusted_relative_humidity: 76.91327524056413,
              wind_speed: 0.9338663816452026,
              wind_direction: 276.8856201171875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T17:00:00+00:00',
              temperature: -4.170204957942279,
              bias_adjusted_temperature: -2.600076499627348,
              relative_humidity: 91.12682600763216,
              bias_adjusted_relative_humidity: 78.70367907035018,
              wind_speed: 0.651400625705719,
              wind_direction: 289.1527099609375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T18:00:00+00:00',
              temperature: -1.8778522544241818,
              bias_adjusted_temperature: -0.629729096038866,
              relative_humidity: 81.92974274465524,
              bias_adjusted_relative_humidity: 74.22128075403184,
              wind_speed: 0.39199328422546387,
              wind_direction: 288.4148254394531,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T19:00:00+00:00',
              temperature: 0.5326442340042254,
              bias_adjusted_temperature: 1.562663783039362,
              relative_humidity: 73.33210578323356,
              bias_adjusted_relative_humidity: 67.24159145375634,
              wind_speed: 1.0261001586914062,
              wind_direction: 266.0942687988281,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T20:00:00+00:00',
              temperature: 2.331300734550116,
              bias_adjusted_temperature: 3.8466616649353838,
              relative_humidity: 64.43140603084484,
              bias_adjusted_relative_humidity: 57.96423345751454,
              wind_speed: 2.05796480178833,
              wind_direction: 266.3709716796875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T21:00:00+00:00',
              temperature: 3.2479838696786683,
              bias_adjusted_temperature: 4.488740064407176,
              relative_humidity: 60.6997925250128,
              bias_adjusted_relative_humidity: 57.64953186962636,
              wind_speed: 2.669013261795044,
              wind_direction: 277.6235046386719,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T22:00:00+00:00',
              temperature: 3.5452506016648764,
              bias_adjusted_temperature: 3.38077205419909,
              relative_humidity: 57.91770215137538,
              bias_adjusted_relative_humidity: 59.97864450706831,
              wind_speed: 3.014889717102051,
              wind_direction: 284.541015625,
              delta_precipitation: 0.000967534937180492
            },
            {
              datetime: '2023-02-18T23:00:00+00:00',
              temperature: 2.5801333446505943,
              bias_adjusted_temperature: 3.914374369167268,
              relative_humidity: 60.07613975472931,
              bias_adjusted_relative_humidity: 55.65779674122943,
              wind_speed: 2.934185028076172,
              wind_direction: 292.011962890625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T00:00:00+00:00',
              temperature: 2.1665844536950862,
              bias_adjusted_temperature: 3.1782371665303293,
              relative_humidity: 63.12046146879156,
              bias_adjusted_relative_humidity: 57.3185007513418,
              wind_speed: 2.449958086013794,
              wind_direction: 284.9099426269531,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T01:00:00+00:00',
              temperature: 1.5693644684086439,
              bias_adjusted_temperature: 3.425358577021862,
              relative_humidity: 64.27019929699658,
              bias_adjusted_relative_humidity: 53.10089707832348,
              wind_speed: 2.1156108379364014,
              wind_direction: 279.744873046875,
              delta_precipitation: 0.0015698077722987591
            },
            {
              datetime: '2023-02-19T02:00:00+00:00',
              temperature: 0.5017985406471827,
              bias_adjusted_temperature: 3.182506580107502,
              relative_humidity: 70.28076465309138,
              bias_adjusted_relative_humidity: 58.473904522321504,
              wind_speed: 1.8907911777496338,
              wind_direction: 275.5021057128906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T03:00:00+00:00',
              temperature: -0.35911913590369754,
              bias_adjusted_temperature: 2.493885382146899,
              relative_humidity: 75.16856098661381,
              bias_adjusted_relative_humidity: 68.12091892385385,
              wind_speed: 1.746675968170166,
              wind_direction: 275.77880859375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T04:00:00+00:00',
              temperature: -1.028052939875875,
              bias_adjusted_temperature: 1.8028267608931599,
              relative_humidity: 79.53391141774586,
              bias_adjusted_relative_humidity: 73.310032128181,
              wind_speed: 1.5276209115982056,
              wind_direction: 271.9972229003906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T05:00:00+00:00',
              temperature: -1.5211279692055966,
              bias_adjusted_temperature: 1.5664781561725587,
              relative_humidity: 82.5614081076387,
              bias_adjusted_relative_humidity: 75.07214176940377,
              wind_speed: 1.1817444562911987,
              wind_direction: 253.36602783203125,
              delta_precipitation: 0.0016778745057806077
            },
            {
              datetime: '2023-02-19T06:00:00+00:00',
              temperature: -1.8554900835404968,
              bias_adjusted_temperature: 0.423997654496338,
              relative_humidity: 82.62640674293513,
              bias_adjusted_relative_humidity: 79.79437846575307,
              wind_speed: 0.7724573612213135,
              wind_direction: 239.34649658203125,
              delta_precipitation: 0.0038294749764764546
            },
            {
              datetime: '2023-02-19T07:00:00+00:00',
              temperature: -2.0795478232109534,
              bias_adjusted_temperature: 0.9170678908292826,
              relative_humidity: 85.04989882257357,
              bias_adjusted_relative_humidity: 78.7612442095669,
              wind_speed: 0.4669331908226013,
              wind_direction: 259.0845031738281,
              delta_precipitation: 0.004194754974908843
            },
            {
              datetime: '2023-02-19T08:00:00+00:00',
              temperature: -2.3193450752058347,
              bias_adjusted_temperature: 0.18465832591977138,
              relative_humidity: 87.03161804983102,
              bias_adjusted_relative_humidity: 81.37124141596782,
              wind_speed: 0.42658093571662903,
              wind_direction: 286.29345703125,
              delta_precipitation: 0.0053991226718870244
            },
            {
              datetime: '2023-02-19T09:00:00+00:00',
              temperature: -2.5092292837189367,
              bias_adjusted_temperature: -0.10010171197708795,
              relative_humidity: 87.95238862651752,
              bias_adjusted_relative_humidity: 81.03466766781132,
              wind_speed: 0.32858261466026306,
              wind_direction: 285.832275390625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T10:00:00+00:00',
              temperature: -2.6086885903924086,
              bias_adjusted_temperature: -0.5205383281954581,
              relative_humidity: 88.54494045957392,
              bias_adjusted_relative_humidity: 80.19656851222459,
              wind_speed: 0.253642737865448,
              wind_direction: 297.6382141113281,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T11:00:00+00:00',
              temperature: -2.6573374784241057,
              bias_adjusted_temperature: -0.7194783098225419,
              relative_humidity: 88.15717573907747,
              bias_adjusted_relative_humidity: 79.88521179530744,
              wind_speed: 0.4669331908226013,
              wind_direction: 283.8953857421875,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T12:00:00+00:00',
              temperature: -2.653666399386647,
              bias_adjusted_temperature: -1.4819845521712587,
              relative_humidity: 87.31815596368685,
              bias_adjusted_relative_humidity: 72.54911974490469,
              wind_speed: 0.6859882473945618,
              wind_direction: 271.1671142578125,
              delta_precipitation: 0.0
            }
          ]
        }
      ]
    },
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
            datetime: '2023-02-17T12:00:00+00:00',
            name: 'High Resolution Deterministic Prediction System',
            abbreviation: 'HRDPS',
            projection: 'ps2.5km'
          },
          values: [
            {
              datetime: '2023-02-17T12:00:00+00:00',
              temperature: -1.2703204323223796,
              bias_adjusted_temperature: 0.20525927024745427,
              relative_humidity: 66.01870695027247,
              bias_adjusted_relative_humidity: 81.14358300875924,
              wind_speed: 1.614090085029602,
              wind_direction: 308.3373107910156,
              delta_precipitation: 0.001781117998082234
            },
            {
              datetime: '2023-02-17T13:00:00+00:00',
              temperature: -2.3350042896413123,
              bias_adjusted_temperature: -0.2312853342615182,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: 85.2585128712741,
              wind_speed: 0.14987978339195251,
              wind_direction: 147.6661834716797,
              delta_precipitation: 0.001309222656307023
            },
            {
              datetime: '2023-02-17T14:00:00+00:00',
              temperature: -2.4237188892506873,
              bias_adjusted_temperature: -0.5627363908242229,
              relative_humidity: 71.31370840827122,
              bias_adjusted_relative_humidity: 84.92658938314982,
              wind_speed: 0.06917528808116913,
              wind_direction: 99.3357162475586,
              delta_precipitation: 0.0011924712592873896
            },
            {
              datetime: '2023-02-17T15:00:00+00:00',
              temperature: -2.5499439731570037,
              bias_adjusted_temperature: -0.7617679759306597,
              relative_humidity: 71.92166295873494,
              bias_adjusted_relative_humidity: 85.7948349346627,
              wind_speed: 0.09223371744155884,
              wind_direction: 42.611976623535156,
              delta_precipitation: 0.0005937059993607447
            },
            {
              datetime: '2023-02-17T16:00:00+00:00',
              temperature: -2.4082986690135093,
              bias_adjusted_temperature: -0.5645736659452201,
              relative_humidity: 72.78944693366184,
              bias_adjusted_relative_humidity: 85.94265231336715,
              wind_speed: 0.19599664211273193,
              wind_direction: 51.835350036621094,
              delta_precipitation: 0.000593706191197506
            },
            {
              datetime: '2023-02-17T17:00:00+00:00',
              temperature: -1.287573403209333,
              bias_adjusted_temperature: 0.3712900774596424,
              relative_humidity: 69.18156453068302,
              bias_adjusted_relative_humidity: 81.9483159311877,
              wind_speed: 0.2305842936038971,
              wind_direction: 25.27203941345215,
              delta_precipitation: 0.0011874119987214894
            },
            {
              datetime: '2023-02-17T18:00:00+00:00',
              temperature: 0.4839150567417877,
              bias_adjusted_temperature: 1.1406056044847095,
              relative_humidity: 62.293685558180044,
              bias_adjusted_relative_humidity: 79.65205334769809,
              wind_speed: 0.26517194509506226,
              wind_direction: 355.37652587890625,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T19:00:00+00:00',
              temperature: 1.2502212617482775,
              bias_adjusted_temperature: 1.2500506303823737,
              relative_humidity: 60.420817093501526,
              bias_adjusted_relative_humidity: 74.51402187432174,
              wind_speed: 0.4611685872077942,
              wind_direction: 311.8421936035156,
              delta_precipitation: 0.0002968528078436117
            },
            {
              datetime: '2023-02-17T20:00:00+00:00',
              temperature: 1.33592342873342,
              bias_adjusted_temperature: 2.2057737992427544,
              relative_humidity: 60.897190360824936,
              bias_adjusted_relative_humidity: 68.5023481757162,
              wind_speed: 0.4611685872077942,
              wind_direction: 248.47763061523438,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T21:00:00+00:00',
              temperature: 1.2533243114387682,
              bias_adjusted_temperature: 2.2213058215002546,
              relative_humidity: 60.812347157067514,
              bias_adjusted_relative_humidity: 67.0552375494227,
              wind_speed: 0.7378697395324707,
              wind_direction: 196.08888244628906,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T22:00:00+00:00',
              temperature: 1.4960745287112789,
              bias_adjusted_temperature: 2.06042881041009,
              relative_humidity: 57.43936241013993,
              bias_adjusted_relative_humidity: 63.04221900205148,
              wind_speed: 0.9915124773979187,
              wind_direction: 183.6373291015625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-17T23:00:00+00:00',
              temperature: 1.491539208427355,
              bias_adjusted_temperature: 2.220354803152416,
              relative_humidity: 55.75096457412904,
              bias_adjusted_relative_humidity: 60.229533346291674,
              wind_speed: 1.1875090599060059,
              wind_direction: 187.41891479492188,
              delta_precipitation: 0.0007205761093489384
            },
            {
              datetime: '2023-02-18T00:00:00+00:00',
              temperature: 1.0736929340052979,
              bias_adjusted_temperature: 2.11428170107105,
              relative_humidity: 55.813537003469996,
              bias_adjusted_relative_humidity: 63.99098303945514,
              wind_speed: 0.9569247961044312,
              wind_direction: 192.58399963378906,
              delta_precipitation: -0.0008474458356636117
            },
            {
              datetime: '2023-02-18T01:00:00+00:00',
              temperature: 0.2896222507433703,
              bias_adjusted_temperature: 1.3898829820308882,
              relative_humidity: 59.50250945644533,
              bias_adjusted_relative_humidity: 65.15301808692044,
              wind_speed: 0.7609281539916992,
              wind_direction: 184.83636474609375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T02:00:00+00:00',
              temperature: -0.38186905707445984,
              bias_adjusted_temperature: 1.5273826795003766,
              relative_humidity: 62.62098002984679,
              bias_adjusted_relative_humidity: 65.99304218851877,
              wind_speed: 0.5764607191085815,
              wind_direction: 179.57904052734375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T03:00:00+00:00',
              temperature: -0.7486534299838582,
              bias_adjusted_temperature: 1.2205498199661289,
              relative_humidity: 64.3009031800602,
              bias_adjusted_relative_humidity: 68.56985506408056,
              wind_speed: 0.553402304649353,
              wind_direction: 180.77809143066406,
              delta_precipitation: 0.00048724263034213323
            },
            {
              datetime: '2023-02-18T04:00:00+00:00',
              temperature: -1.0739074534190811,
              bias_adjusted_temperature: 0.9456868928184233,
              relative_humidity: 68.2821469852489,
              bias_adjusted_relative_humidity: 74.55119434381218,
              wind_speed: 0.749398946762085,
              wind_direction: 166.11293029785156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T05:00:00+00:00',
              temperature: -1.4131158947399338,
              bias_adjusted_temperature: 0.765738961468325,
              relative_humidity: 71.77719726909814,
              bias_adjusted_relative_humidity: 79.83029739370673,
              wind_speed: 0.8646910786628723,
              wind_direction: 155.13711547851562,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T06:00:00+00:00',
              temperature: -1.6877098544356826,
              bias_adjusted_temperature: -0.2637740087112086,
              relative_humidity: 75.13296943397938,
              bias_adjusted_relative_humidity: 82.8221350821199,
              wind_speed: 0.807045042514801,
              wind_direction: 150.98660278320312,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T07:00:00+00:00',
              temperature: -1.9007479347008753,
              bias_adjusted_temperature: 0.23055328485508952,
              relative_humidity: 76.97755894631018,
              bias_adjusted_relative_humidity: 85.28824004637389,
              wind_speed: 0.8531618714332581,
              wind_direction: 147.20501708984375,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T08:00:00+00:00',
              temperature: -2.0935038096056564,
              bias_adjusted_temperature: 0.07455057045492253,
              relative_humidity: 78.69240675771891,
              bias_adjusted_relative_humidity: 86.8529765868017,
              wind_speed: 0.8589264750480652,
              wind_direction: 142.03993225097656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T09:00:00+00:00',
              temperature: -2.2365582491659333,
              bias_adjusted_temperature: -0.30591277499075287,
              relative_humidity: 81.38405438403697,
              bias_adjusted_relative_humidity: 89.47264134935708,
              wind_speed: 0.7263405323028564,
              wind_direction: 141.7632293701172,
              delta_precipitation: 0.0015476155877164905
            },
            {
              datetime: '2023-02-18T10:00:00+00:00',
              temperature: -2.3013214724910664,
              bias_adjusted_temperature: -0.0789737348620192,
              relative_humidity: 83.72757879125446,
              bias_adjusted_relative_humidity: 90.24080939419883,
              wind_speed: 0.749398946762085,
              wind_direction: 141.7632293701172,
              delta_precipitation: 0.0005937056156872216
            },
            {
              datetime: '2023-02-18T11:00:00+00:00',
              temperature: -2.3070110669109,
              bias_adjusted_temperature: 0.1335230436877941,
              relative_humidity: 84.22651492229467,
              bias_adjusted_relative_humidity: 87.14117444191146,
              wind_speed: 0.7321051359176636,
              wind_direction: 139.36514282226562,
              delta_precipitation: 0.0036889360237731626
            },
            {
              datetime: '2023-02-18T12:00:00+00:00',
              temperature: -2.282127745338259,
              bias_adjusted_temperature: -0.6764213017091192,
              relative_humidity: 85.20332045969857,
              bias_adjusted_relative_humidity: 89.08953580587935,
              wind_speed: 0.507285475730896,
              wind_direction: 137.9816436767578,
              delta_precipitation: 0.04553830985229334
            },
            {
              datetime: '2023-02-18T13:00:00+00:00',
              temperature: -2.3045094002495423,
              bias_adjusted_temperature: -0.2016320977508692,
              relative_humidity: 84.59536276618137,
              bias_adjusted_relative_humidity: 89.94422290743655,
              wind_speed: 0.3804640769958496,
              wind_direction: 160.11773681640625,
              delta_precipitation: 0.029386147588713822
            },
            {
              datetime: '2023-02-18T14:00:00+00:00',
              temperature: -2.3733071373104453,
              bias_adjusted_temperature: -0.5152782643338183,
              relative_humidity: 86.3102111412025,
              bias_adjusted_relative_humidity: 89.900795813503,
              wind_speed: 0.26517194509506226,
              wind_direction: 128.66603088378906,
              delta_precipitation: 0.082622399636629
            },
            {
              datetime: '2023-02-18T15:00:00+00:00',
              temperature: -2.4718382584865317,
              bias_adjusted_temperature: -0.6918436210069516,
              relative_humidity: 86.91816569166622,
              bias_adjusted_relative_humidity: 91.23825178699035,
              wind_speed: 0.24211350083351135,
              wind_direction: 159.37986755371094,
              delta_precipitation: 0.10335669619519625
            },
            {
              datetime: '2023-02-18T16:00:00+00:00',
              temperature: -2.238853005394742,
              bias_adjusted_temperature: -0.41084079662040685,
              relative_humidity: 88.13407479259365,
              bias_adjusted_relative_humidity: 92.84259810961709,
              wind_speed: 0.057646073400974274,
              wind_direction: 219.331787109375,
              delta_precipitation: 0.19120744729726868
            },
            {
              datetime: '2023-02-18T17:00:00+00:00',
              temperature: -1.443984620643355,
              bias_adjusted_temperature: 0.21237987701816974,
              relative_humidity: 85.90556260062068,
              bias_adjusted_relative_humidity: 94.14702970097251,
              wind_speed: 0.2709365487098694,
              wind_direction: 325.8617248535156,
              delta_precipitation: 0.1432024843415543
            },
            {
              datetime: '2023-02-18T18:00:00+00:00',
              temperature: -0.7486900963848496,
              bias_adjusted_temperature: -0.02067613492927156,
              relative_humidity: 78.92115831547478,
              bias_adjusted_relative_humidity: 90.48952709606982,
              wind_speed: 0.5879899263381958,
              wind_direction: 319.03643798828125,
              delta_precipitation: 0.010833977454479227
            },
            {
              datetime: '2023-02-18T19:00:00+00:00',
              temperature: 0.5043788444701202,
              bias_adjusted_temperature: 0.5604446535333865,
              relative_humidity: 63.94325010565244,
              bias_adjusted_relative_humidity: 77.12653894066959,
              wind_speed: 1.1586860418319702,
              wind_direction: 327.7063903808594,
              delta_precipitation: 0.021200976039987274
            },
            {
              datetime: '2023-02-18T20:00:00+00:00',
              temperature: 1.4767933775153783,
              bias_adjusted_temperature: 2.3324237693001537,
              relative_humidity: 59.11392684183834,
              bias_adjusted_relative_humidity: 66.37120751762556,
              wind_speed: 1.6486777067184448,
              wind_direction: 325.8617248535156,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T21:00:00+00:00',
              temperature: 1.6660471324449677,
              bias_adjusted_temperature: 2.58953617386019,
              relative_humidity: 58.75467791622138,
              bias_adjusted_relative_humidity: 64.3314072223518,
              wind_speed: 1.9426727294921875,
              wind_direction: 338.7744445800781,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-18T22:00:00+00:00',
              temperature: 1.618045190975773,
              bias_adjusted_temperature: 2.168684322103778,
              relative_humidity: 59.0471089832802,
              bias_adjusted_relative_humidity: 65.24190686248582,
              wind_speed: 1.9542019367218018,
              wind_direction: 344.7696228027344,
              delta_precipitation: 0.0004872423154689276
            },
            {
              datetime: '2023-02-18T23:00:00+00:00',
              temperature: 1.4006313915563904,
              bias_adjusted_temperature: 2.1389415252935873,
              relative_humidity: 60.40266671400459,
              bias_adjusted_relative_humidity: 66.82878794176779,
              wind_speed: 1.7927929162979126,
              wind_direction: 343.8472900390625,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T00:00:00+00:00',
              temperature: 0.9810608924510922,
              bias_adjusted_temperature: 2.0191882314369183,
              relative_humidity: 64.80317328210927,
              bias_adjusted_relative_humidity: 73.54279060421567,
              wind_speed: 1.4296226501464844,
              wind_direction: 342.0948486328125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T01:00:00+00:00',
              temperature: -0.19824060919913603,
              bias_adjusted_temperature: 0.8767854457284402,
              relative_humidity: 72.38605790670398,
              bias_adjusted_relative_humidity: 77.36248644016123,
              wind_speed: 1.1586860418319702,
              wind_direction: 331.48797607421875,
              delta_precipitation: 0.0011873866762690533
            },
            {
              datetime: '2023-02-19T02:00:00+00:00',
              temperature: -1.233134016275564,
              bias_adjusted_temperature: 0.6167859367283293,
              relative_humidity: 75.47099096876198,
              bias_adjusted_relative_humidity: 78.28043803958414,
              wind_speed: 0.9742186665534973,
              wind_direction: 329.2743835449219,
              delta_precipitation: 0.0035622582492287336
            },
            {
              datetime: '2023-02-19T03:00:00+00:00',
              temperature: -1.6818404320322793,
              bias_adjusted_temperature: 0.27114801228729024,
              relative_humidity: 74.83245186425877,
              bias_adjusted_relative_humidity: 80.36137057055471,
              wind_speed: 0.7724573612213135,
              wind_direction: 328.1675720214844,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T04:00:00+00:00',
              temperature: -1.8914375936068337,
              bias_adjusted_temperature: 0.1849862320713147,
              relative_humidity: 75.33001632650328,
              bias_adjusted_relative_humidity: 82.3971199399091,
              wind_speed: 0.5361084938049316,
              wind_direction: 326.4151306152344,
              delta_precipitation: 0.0011874357864798402
            },
            {
              datetime: '2023-02-19T05:00:00+00:00',
              temperature: -2.0935502988706864,
              bias_adjusted_temperature: 0.07496622170702016,
              relative_humidity: 74.77308096933059,
              bias_adjusted_relative_humidity: 82.3362442828628,
              wind_speed: 0.36893486976623535,
              wind_direction: 318.7597351074219,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T06:00:00+00:00',
              temperature: -2.3206158612560768,
              bias_adjusted_temperature: -0.8332864712079591,
              relative_humidity: 75.32736031615613,
              bias_adjusted_relative_humidity: 83.08366563617633,
              wind_speed: 0.28823035955429077,
              wind_direction: 314.2402648925781,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T07:00:00+00:00',
              temperature: -2.872025267924057,
              bias_adjusted_temperature: -0.755738075002168,
              relative_humidity: 76.22471072060459,
              bias_adjusted_relative_humidity: 84.84606800043451,
              wind_speed: 0.22481968998908997,
              wind_direction: 315.53155517578125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T08:00:00+00:00',
              temperature: -3.4113521586534783,
              bias_adjusted_temperature: -1.1748990284503096,
              relative_humidity: 77.1870721031679,
              bias_adjusted_relative_humidity: 85.87190759990582,
              wind_speed: 0.08646911382675171,
              wind_direction: 315.53155517578125,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T09:00:00+00:00',
              temperature: -3.5937990928967207,
              bias_adjusted_temperature: -1.6275932350062223,
              relative_humidity: 78.52625841534848,
              bias_adjusted_relative_humidity: 87.93892523617012,
              wind_speed: 0.04611685872077942,
              wind_direction: 80.24333190917969,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T10:00:00+00:00',
              temperature: -3.7247744714409947,
              bias_adjusted_temperature: -1.3805619921384538,
              relative_humidity: 79.15434057813698,
              bias_adjusted_relative_humidity: 88.10434120004837,
              wind_speed: 0.12105675041675568,
              wind_direction: 108.65132141113281,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T11:00:00+00:00',
              temperature: -4.290300403510954,
              bias_adjusted_temperature: -1.7522048811807083,
              relative_humidity: 76.97810187094792,
              bias_adjusted_relative_humidity: 84.89207606082927,
              wind_speed: 0.10952754318714142,
              wind_direction: 135.03016662597656,
              delta_precipitation: 0.0
            },
            {
              datetime: '2023-02-19T12:00:00+00:00',
              temperature: -5.017272154094691,
              bias_adjusted_temperature: -3.0598036470177346,
              relative_humidity: 75.68429381528576,
              bias_adjusted_relative_humidity: 85.14691082915677,
              wind_speed: 0.17293822765350342,
              wind_direction: 144.9914093017578,
              delta_precipitation: 0.0
            }
          ]
        }
      ]
    }
  ]
}
