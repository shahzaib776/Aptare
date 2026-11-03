import { FIRST_BULLET_ID, fixtureResume } from "./fixtureResume";
import { textOf, withText } from "./resumeText";

test("finds the text of a bullet by its id", () => {
  expect(textOf(fixtureResume, FIRST_BULLET_ID)).toMatch(/^Cut nightly batch time/);
});

test("finds the summary by the id 'summary'", () => {
  expect(textOf(fixtureResume, "summary")).toBe(fixtureResume.summary);
});

test("an unknown id has no text", () => {
  expect(textOf(fixtureResume, "nope")).toBeUndefined();
});

test("changes the targeted bullet and nothing else", () => {
  const original = textOf(fixtureResume, FIRST_BULLET_ID) ?? "";

  const changed = withText(fixtureResume, FIRST_BULLET_ID, "New text");

  expect(textOf(changed, FIRST_BULLET_ID)).toBe("New text");
  expect(withText(changed, FIRST_BULLET_ID, original)).toEqual(fixtureResume);
});

test("changes the summary", () => {
  expect(withText(fixtureResume, "summary", "Short.").summary).toBe("Short.");
});

test("does not mutate the resume it was given", () => {
  const before = JSON.stringify(fixtureResume);

  withText(fixtureResume, FIRST_BULLET_ID, "New text");
  withText(fixtureResume, "summary", "New summary");

  expect(JSON.stringify(fixtureResume)).toBe(before);
});

test("an unknown id changes nothing", () => {
  expect(withText(fixtureResume, "nope", "x")).toEqual(fixtureResume);
});
