import { fireZoneUnitNameFormatter, nameFormatter } from "@/utils/stringUtils";

describe("nameFormatter", () => {
  it("removes specified suffix and returns output in upper case", () => {
    const prefix = "Coastal";
    const suffix = "Fire Centre";
    const input = `${prefix} ${suffix}`;
    const result = nameFormatter(input, suffix, true);
    expect(result).toBe(prefix.toLocaleUpperCase());
  });
  it("returns input as uppercase if suffix is empty", () => {
    const prefix = "Coastal";
    const suffix = "";
    const input = `${prefix} ${suffix}`;
    const result = nameFormatter(input, suffix, true);
    expect(result).toBe(prefix.toLocaleUpperCase());
  });
  it("returns input as uppercase if suffix doesn't match", () => {
    const prefix = "Coastal";
    const suffix = "Fire Centre";
    const input = `${prefix}`;
    const result = nameFormatter(input, suffix, true);
    expect(result).toBe(prefix.toLocaleUpperCase());
  });
  it("trims whitespace from the output", () => {
    const prefix = "Coastal";
    const suffix = "Fire Centre";
    const input = `   ${prefix}     ${suffix}  `;
    const result = nameFormatter(input, suffix, true);
    expect(result).toBe(prefix.toLocaleUpperCase());
  });
  it("returns an empty string if the input is empty", () => {
    const result = nameFormatter("", "foo", true);
    expect(result).toBe("");
  });
  it("does not capitalize output when isUpper is false", () => {
    const prefix = "Kamloops";
    const suffix = "Fire Zone";
    const input = `${prefix}`;
    const result = nameFormatter(input, suffix, false);
    expect(result).toBe(prefix);
  });
  it("returns an empty string if suffix at index 0", () => {
    const suffix = "Fire Centre";
    const input = `${suffix}`;
    const result = nameFormatter(input, suffix, true);
    expect(result).toBe("");
  });
});

describe("fireZoneUnitNameFormatter", () => {
  it("returns an empty string when the input is undefined", () => {
    expect(fireZoneUnitNameFormatter(undefined)).toBe("");
  });

  it("moves bracketed text to a second line after removing the zone suffix", () => {
    const result = fireZoneUnitNameFormatter("G4-VanJam Zone (Vanderhoof)");

    expect(result).toBe("G4-VanJam\n(Vanderhoof)");
  });

  it("removes Zone when that is the suffix in the source name", () => {
    const result = fireZoneUnitNameFormatter("K7-Lillooet Zone");

    expect(result).toBe("K7-Lillooet");
  });

  it("removes redundant duplicate locations for Kamloops and Vernon", () => {
    expect(fireZoneUnitNameFormatter("K2-Kamloops Zone (Kamloops)")).toBe(
      "K2-Kamloops",
    );

    expect(fireZoneUnitNameFormatter("K4-Vernon Zone (Vernon)")).toBe(
      "K4-Vernon",
    );
  });

  it("treats whitespace differences as redundant duplicate locations", () => {
    expect(fireZoneUnitNameFormatter("K2 - Kamloops Zone (Kamloops)")).toBe(
      "K2 - Kamloops",
    );

    expect(fireZoneUnitNameFormatter("K4 - Vernon Zone (Vernon)")).toBe(
      "K4 - Vernon",
    );
  });

  it("removes the zone suffix when there is no bracketed suffix", () => {
    const result = fireZoneUnitNameFormatter("Kamloops Zone");

    expect(result).toBe("Kamloops");
  });
});
