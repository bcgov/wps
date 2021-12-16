export const logError = (err: unknown): void => {
  if (import.meta.env.NODE_ENV !== 'test') {
    console.error(err)
  }
}
