export const logError = (err: unknown): void => {
  if (process.env.NODE_ENV !== 'test') {
    console.error(err)
  }
}
