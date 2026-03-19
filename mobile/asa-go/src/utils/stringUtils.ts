import { isNil } from "lodash";

const ZONE_SUFFIX = "Zone";

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

const stripZoneSuffix = (input: string) => {
  const trimmedInput = input.trim();

  if (!trimmedInput.endsWith(ZONE_SUFFIX)) {
    return trimmedInput;
  }

  return trimmedInput.slice(0, -ZONE_SUFFIX.length).trim();
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

export const fireZoneUnitNameFormatter = (input: string) => {
  if (isNil(input) || input === "") {
    return "";
  }

  const { baseName, bracketedSuffix } = splitBracketedSuffix(input);
  const formattedBaseName = stripZoneSuffix(baseName);
  const isRedundantLocation = FIRE_ZONE_UNITS_WITH_REDUNDANT_LOCATION.has(
    `${formattedBaseName}|${bracketedSuffix}`,
  );

  const output =
    bracketedSuffix && !isRedundantLocation
      ? `${formattedBaseName}\n${bracketedSuffix}`
      : formattedBaseName;

  return output.trim();
};
