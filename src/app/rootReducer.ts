import { combineReducers } from '@reduxjs/toolkit'

const rootReducer = combineReducers({})

// infer whatever gets returned from rootReducer and use it as the type of the root state
export type RootState = ReturnType<typeof rootReducer>

export default rootReducer
