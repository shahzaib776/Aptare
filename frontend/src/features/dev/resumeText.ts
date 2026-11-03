import type { TailoredResume } from "../../api/types";

// The ids the backend's text map uses: "summary", or a bullet's own id.
const SUMMARY_ID = "summary";

type Bullet = { id: string; text: string };

function allBullets(resume: TailoredResume): Bullet[] {
  return resume.sections.flatMap((section) =>
    section.key === "experience" || section.key === "projects"
      ? section.items.flatMap((item) => item.bullets)
      : [],
  );
}

export function textOf(resume: TailoredResume, id: string): string | undefined {
  if (id === SUMMARY_ID) return resume.summary ?? undefined;
  return allBullets(resume).find((bullet) => bullet.id === id)?.text;
}

/** A copy of the resume with one element's text replaced; the input is never changed. */
export function withText(resume: TailoredResume, id: string, text: string): TailoredResume {
  if (id === SUMMARY_ID) return { ...resume, summary: text };
  const replace = <B extends Bullet>(bullets: B[]): B[] =>
    bullets.map((bullet) => (bullet.id === id ? { ...bullet, text } : bullet));
  return {
    ...resume,
    sections: resume.sections.map((section) => {
      if (section.key === "experience") {
        return {
          ...section,
          items: section.items.map((item) => ({ ...item, bullets: replace(item.bullets) })),
        };
      }
      if (section.key === "projects") {
        return {
          ...section,
          items: section.items.map((item) => ({ ...item, bullets: replace(item.bullets) })),
        };
      }
      return section;
    }),
  };
}
