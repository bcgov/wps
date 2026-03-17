import { isNil } from "lodash";

export const nameFormatter = (
  input: string,
  suffix: string,
  toUpper: boolean,
) => {
  if (isNil(input) || input === "") {
    return "";
  }
  let output: string;
  const index = input.indexOf(suffix);
  if (index < 0 || suffix === "") {
    output = input;
  } else {
    output = input.substring(0, index);
  }

  return toUpper ? output.trim().toUpperCase() : output.trim();
};
