export interface ColorBreak {
  min: number
  max: number | null
  color: string
  label: string
}

export const FWI_COLOR_BREAKS: ColorBreak[] = [
  { min: 0, max: 8, color: 'rgb(0, 0, 255)', label: '0-8' },
  { min: 8, max: 17, color: 'rgb(0, 127, 255)', label: '8-17' },
  { min: 17, max: 27, color: 'rgb(0, 255, 0)', label: '17-27' },
  { min: 27, max: 38, color: 'rgb(255, 255, 0)', label: '27-38' },
  { min: 38, max: 47, color: 'rgb(255, 170, 0)', label: '38-47' },
  { min: 47, max: null, color: 'rgb(255, 0, 0)', label: '47+' }
]
