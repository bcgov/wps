// A Map of fuel type codes to the colour typically used in BCWS
export const colorByFuelTypeCode = new Map<string, [number, number, number]>([
  ['C-1', [209, 255, 115]],
  ['C-2', [34, 102, 51]],
  ['C-3', [131, 199, 149]],
  ['C-4', [112, 168, 0]],
  ['C-5', [223, 184, 230]],
  ['C-6', [172, 102, 237]],
  ['C-7', [112, 12, 242]],
  ['D-1/D-2', [137, 112, 68]],
  ['S-1', [251, 190, 185]],
  ['S-2', [247, 104, 161]],
  ['S-3', [174, 1, 126]],
  ['O-1a/O-1b', [255, 255, 190]],
  ['M-1/M-2', [255, 211, 127]]
])

// Retrieve a color from the Map based on the fuel type code.
// Provide a default value in case a non-standard code is encountered so we don't end up with empty pie slices.
export const getColorByFuelTypeCode = (code: string): string => {
  for (const [key, color] of colorByFuelTypeCode.entries()) {
    if (code.startsWith(key)) {
      return `rgb(${color[0]}, ${color[1]}, ${color[2]})`
    }
  }
  return 'rgb(0, 255, 255)'
}
