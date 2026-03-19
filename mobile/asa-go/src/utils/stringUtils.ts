import { isNil } from "lodash";

const FIRE_ZONE_UNITS_WITH_REDUNDANT_LOCATION = new Set([
  "K2-Kamloops|(Kamloops)",
  "K4-Vernon|(Vernon)",
]);

const splitBracketedSuffix = (input: string) => {
  const trimmedInput = input.trim();
  const bracketIndex = trimmedInput.indexOf("(");

  if (bracketIndex <= 0) {
    return {
      baseName: trimmedInput,
      bracketedSuffix: "",
    };
  }

  return {
    baseName: trimmedInput.substring(0, bracketIndex).trim(),
    bracketedSuffix: trimmedInput.substring(bracketIndex).trim(),
  };
};

const removeSuffix = (input: string, suffix: string) => {
  if (suffix === "") {
    return input.trim();
  }

  const suffixIndex = input.indexOf(suffix);

  if (suffixIndex < 0) {
    return input.trim();
  }

  return input.substring(0, suffixIndex).trim();
};

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

export const fireZoneUnitNameFormatter = (
  input: string,
  suffix: string,
  toUpper: boolean,
) => {
  if (isNil(input) || input === "") {
    return "";
  }

  const { baseName, bracketedSuffix } = splitBracketedSuffix(input);
  const formattedBaseName = removeSuffix(baseName, suffix);
  const isRedundantLocation = FIRE_ZONE_UNITS_WITH_REDUNDANT_LOCATION.has(
    `${formattedBaseName}|${bracketedSuffix}`,
  );

  const output =
    bracketedSuffix && !isRedundantLocation
      ? `${formattedBaseName}\n${bracketedSuffix}`
      : formattedBaseName;

  return toUpper ? output.trim().toUpperCase() : output.trim();
};
