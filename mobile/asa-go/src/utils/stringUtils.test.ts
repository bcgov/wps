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
  it("moves bracketed text to a second line after removing the suffix", () => {
    const result = fireZoneUnitNameFormatter(
      "G4-VanJam Fire Zone (Vanderhoof)",
      "Fire Zone",
      false,
    );

    expect(result).toBe("G4-VanJam\n(Vanderhoof)");
  });

  it("removes redundant duplicate locations for Kamloops and Vernon", () => {
    expect(
      fireZoneUnitNameFormatter(
        "K2-Kamloops Fire Zone (Kamloops)",
        "Fire Zone",
        false,
      ),
    ).toBe("K2-Kamloops");

    expect(
      fireZoneUnitNameFormatter(
        "K4-Vernon Fire Zone (Vernon)",
        "Fire Zone",
        false,
      ),
    ).toBe("K4-Vernon");
  });

  it("keeps bracketed text inline when there is no bracketed suffix", () => {
    const result = fireZoneUnitNameFormatter(
      "Kamloops Fire Zone",
      "Fire Zone",
      false,
    );

    expect(result).toBe("Kamloops");
  });
});
