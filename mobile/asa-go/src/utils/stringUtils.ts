import { isNil } from "lodash";

export const nameFormatter = (input: string, suffix: string) => {
  if (isNil(input) || input === "") {
    return "";
  }
  const index = input.indexOf(suffix);
  if (index <= 0) {
    return input.trim().toUpperCase();
  }
  const output = input.substring(0, index);
  return output.trim().toUpperCase();
};
