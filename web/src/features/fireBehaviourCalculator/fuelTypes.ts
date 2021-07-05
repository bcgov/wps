export interface FBCFuelType {
  name: string
  friendlyName: string
}

export class FuelTypes {
  get(): FBCFuelType[] {
    return [
      { name: 'c2', friendlyName: 'C2' },
      { name: 'c3', friendlyName: 'C3' },
      { name: 'c4', friendlyName: 'C4' },
      { name: 'c5', friendlyName: 'C5' },
      { name: 'c6_7mcbh', friendlyName: 'C6 7-m CBH' },
      { name: 'c6_2mcbh', friendlyName: 'C6 2-m CBH' },
      { name: 'c7', friendlyName: 'C7' },
      { name: 'd1', friendlyName: 'D1' },
      { name: 'd2', friendlyName: 'D2' },
      { name: 'm1_75conifer', friendlyName: 'M1 75% conifer / 25% deciduous' },
      { name: 'm1_50conider', friendlyName: 'M1 50% conifer / 50% deciduous' },
      { name: 'm1_25confier', friendlyName: 'M1 25% conifer / 75% deciduous' },
      { name: 'm2_75confier', friendlyName: 'M2 75% conifer / 75% deciduous' },
      { name: 'm2_50confier', friendlyName: 'M2 50% conifer / 50% deciduous' },
      { name: 'm2_25confier', friendlyName: 'M2 25% conifer / 75% deciduous' },
      { name: 'm3_30deadfir', friendlyName: 'M3 30% dead fir' },
      { name: 'm3_60deadfir', friendlyName: 'M3 60% dead fir' },
      { name: 'm3_100deadfir', friendlyName: 'M3 100% dead fir' },
      { name: 'm4_30deadfir', friendlyName: 'M4 30% dead fir' },
      { name: 'm4_60deadfir', friendlyName: 'M4 60% dead fir' },
      { name: 'm4_100deadfir', friendlyName: 'M4 100% dead fir' },
      { name: 'o1a_0curing', friendlyName: 'O1A 0% curing' },
      { name: 'o1a_30curing', friendlyName: 'O1A 30% curing' },
      { name: 'o1a_90curing', friendlyName: 'O1A 90% curing' },
      { name: 'o1b_0curing', friendlyName: 'O1B 0% curing' },
      { name: 'o1b_30curing', friendlyName: 'O1B 30% curing' },
      { name: 'o1b_90curing', friendlyName: 'O1B 90% curing' },
      { name: 's1', friendlyName: 'S1' },
      { name: 's2', friendlyName: 'S2' },
      { name: 's3', friendlyName: 'S3' }
    ]
  }
}
