// A Map of fuel type codes to the colour typically used in BCWS
const colorByFuelTypeCode = new Map()
colorByFuelTypeCode.set('C-1', 'rgb(209, 255, 115)')
colorByFuelTypeCode.set('C-2', 'rgb(34, 102, 51)')
colorByFuelTypeCode.set('C-3', 'rgb(131, 199, 149)')
colorByFuelTypeCode.set('C-4', 'rgb(112, 168, 0)')
colorByFuelTypeCode.set('C-5', 'rgb(223, 184, 230)')
colorByFuelTypeCode.set('C-6', 'rgb(172, 102, 237)')
colorByFuelTypeCode.set('C-7', 'rgb(112, 12, 242)')
colorByFuelTypeCode.set('D-1/D-2', 'rgb(137, 112, 68)')
colorByFuelTypeCode.set('S-1', 'rgb(251, 190, 185)')
colorByFuelTypeCode.set('S-2', 'rgb(247, 104, 161)')
colorByFuelTypeCode.set('S-3', 'rgb(174, 1, 126)')
colorByFuelTypeCode.set('O-1a/O-1b', 'rgb(255, 255, 190)')
colorByFuelTypeCode.set('M-1/M-2', 'rgb(255, 211, 127)')

// Retrieve a color from the Map base don the fuel type code.
// Provide a default value in case a non-standard code is encountered so we don't end up with empty pie slices.
export const getColorByFuelTypeCode = (code: string): string => {
  const color = colorByFuelTypeCode.get(code)
  return color ?? 'rgb(0, 255, 255)'
}
