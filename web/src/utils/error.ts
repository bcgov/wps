export const logError = (err: unknown): void => {
  if (import.meta.env.MODE !== 'test') {
    console.error(err)
  }
}
