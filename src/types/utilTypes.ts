// Utility type that makes all properties, including nested ones, optional
export type RecursivePartial<T> = {
  [P in keyof T]?: RecursivePartial<T[P]>
}
