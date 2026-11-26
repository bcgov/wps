// The years drawn beside the selected one, and the colours they are drawn in.

// The colours stay apart from one another for colour-blind readers, and have a contrast of at
// least 3 with the darkest band behind them.
export const COMPARED_YEAR_COLOURS = ['#217fd8', '#88341e', '#598332', '#6724ad', '#cc3a92']

// As many as there are colours, which is also the most the API compares in one request.
export const MAX_COMPARED_YEARS = COMPARED_YEAR_COLOURS.length
// Charts of each station are small, so each compares one year.
export const MAX_COMPARED_YEARS_EACH = 1

export interface ComparedYear {
  year: number
  colour: string
}

/**
 * The years chosen, newest first, with their colours. A year already compared keeps its colour,
 * and a new one takes the first that is free, so that a line does not change colour when another
 * is added or removed. Years past the most that can be compared are left out.
 */
export const chooseComparedYears = (current: ComparedYear[], years: number[]): ComparedYear[] => {
  const kept = current.filter(({ year }) => years.includes(year))
  const free = COMPARED_YEAR_COLOURS.filter(colour => !kept.some(each => each.colour === colour))
  const added = years
    .filter(year => !kept.some(each => each.year === year))
    .slice(0, free.length)
    .map((year, index) => ({ year, colour: free[index] }))
  return [...kept, ...added].sort((a, b) => b.year - a.year)
}

/** The `count` years before `year`, newest first, back to `firstYear`. */
export const yearsBefore = (year: number, count: number, firstYear: number): number[] =>
  Array.from({ length: count }, (_, index) => year - 1 - index).filter(each => each >= firstYear)
