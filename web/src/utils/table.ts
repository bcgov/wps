export type Order = 'asc' | 'desc'

// More generic approach https://material-ui.com/components/tables/#EnhancedTable.tsx
export const getDatetimeComparator = (order: Order) => <T extends { datetime: string }>(
  a: T,
  b: T
): number => {
  const aDate = new Date(a.datetime)
  const bDate = new Date(b.datetime)
  const diff = aDate.valueOf() - bDate.valueOf()

  return order === 'asc' ? diff : -diff
}
