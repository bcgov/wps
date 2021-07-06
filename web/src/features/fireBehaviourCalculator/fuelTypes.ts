export interface FBCFuelType {
  name: string
  friendlyName: string
  percentage_conifer: number | undefined
  percentage_dead_balsam_fir: number | undefined
  crown_base_height: number | undefined
}
export class FuelTypes {
  static lookup(key: string): FBCFuelType {
    return FuelTypes.get()[key]
  }
  static get(): Record<string, FBCFuelType> {
    return {
      c1: {
        name: 'C1',
        friendlyName: 'C1',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 2
      },
      c2: {
        name: 'C2',
        friendlyName: 'C2',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 3
      },
      c3: {
        name: 'C3',
        friendlyName: 'C3',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 8
      },
      c4: {
        name: 'C4',
        friendlyName: 'C4',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 4
      },
      c5: {
        name: 'C5',
        friendlyName: 'C5',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 18
      },
      c6_7mcbh: {
        name: 'C6',
        friendlyName: 'C6 7-m CBH',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 7
      },
      c6_2mcbh: {
        name: 'C6',
        friendlyName: 'C6 2-m CBH',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 2
      },
      c7: {
        name: 'C7',
        friendlyName: 'C7',
        percentage_conifer: 100,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 10
      },
      d1: {
        name: 'D1',
        friendlyName: 'D1',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      },
      m1_75conifer: {
        name: 'M1',
        friendlyName: 'M1 75% conifer / 25% deciduous',
        percentage_conifer: 75,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m1_50conifer: {
        name: 'M1',
        friendlyName: 'M1 50% conifer / 50% deciduous',
        percentage_conifer: 50,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m1_25conifer: {
        name: 'M1',
        friendlyName: 'M1 25% conifer / 75% deciduous',
        percentage_conifer: 25,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m2_75conifer: {
        name: 'M2',
        friendlyName: 'M2 75% conifer / 25% deciduous',
        percentage_conifer: 75,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m2_50conider: {
        name: 'M2',
        friendlyName: 'M2 50% conifer / 50% deciduous',
        percentage_conifer: 50,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m2_25confier: {
        name: 'M2',
        friendlyName: 'M2 25% conifer / 75% deciduous',
        percentage_conifer: 25,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: 6
      },
      m3_30deadfir: {
        name: 'M3',
        friendlyName: 'M3 30% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 30,
        crown_base_height: 6
      },
      m3_60deadfir: {
        name: 'M3',
        friendlyName: 'M3 60% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 60,
        crown_base_height: 6
      },
      m3_100deadfir: {
        name: 'M3',
        friendlyName: 'M3 100% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 100,
        crown_base_height: 6
      },
      m4_30deadfir: {
        name: 'M4',
        friendlyName: 'M4 30% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 30,
        crown_base_height: 6
      },
      m4_60deadfir: {
        name: 'M4',
        friendlyName: 'M4 60% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 60,
        crown_base_height: 6
      },
      m4_100deadfir: {
        name: 'M4',
        friendlyName: 'M4 100% dead fir',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: 100,
        crown_base_height: 6
      },
      o1a: {
        name: 'O1A',
        friendlyName: 'O1A',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      },
      o1b: {
        name: 'O1B',
        friendlyName: 'O1B',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      },
      s1: {
        name: 'S1',
        friendlyName: 'S1',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      },
      s2: {
        name: 'S2',
        friendlyName: 'S2',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      },
      s3: {
        name: 'S3',
        friendlyName: 'S3',
        percentage_conifer: undefined,
        percentage_dead_balsam_fir: undefined,
        crown_base_height: undefined
      }
    }
  }
}
