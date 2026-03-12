import { nameFormatter } from "@/utils/stringUtils";

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
});
