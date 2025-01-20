// top-level declaration for *.pdf
declare module '*.pdf'

// Utility type that makes all properties, including nested ones, optional
declare type RecursivePartial<T> = {
  [P in keyof T]?: RecursivePartial<T[P]>
}

declare type ValueOf<T> = T[keyof T]
