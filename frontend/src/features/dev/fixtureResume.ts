import type { TailoredResume } from "../../api/types";

// Fixed ids so tests and the playground always agree. The long bullets wrap onto a second line
// and "multi-threaded" can break at its hyphen, so the click regions can be seen spanning lines.
export const fixtureResume: TailoredResume = {
  header: {
    full_name: "Ada Lovelace",
    headline: "Software Engineer",
    email: "ada@example.com",
    phone: "555-0100",
    location: "London",
    links: [
      { kind: "linkedin", label: "linkedin.com/in/ada", url: "https://linkedin.com/in/ada" },
      { kind: "github", label: "github.com/ada", url: "https://github.com/ada" },
    ],
  },
  summary: "Engineer who builds reliable data systems and keeps them fast.",
  sections: [
    {
      key: "experience",
      items: [
        {
          experience_id: "00000000-0000-4000-8000-000000000001",
          variant_id: "00000000-0000-4000-8000-000000000002",
          title: "Senior Engineer",
          company: "Analytical Engines Ltd",
          location: "London",
          dates: "2021 - Present",
          bullets: [
            {
              id: "00000000-0000-4000-8000-000000000010",
              source_bullet_id: "00000000-0000-4000-8000-000000000110",
              text: "Cut nightly batch time from 4 hours to 55 minutes by redesigning the multi-threaded ingestion pipeline and caching hot partitions",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
            {
              id: "00000000-0000-4000-8000-000000000011",
              source_bullet_id: "00000000-0000-4000-8000-000000000111",
              text: "Led a team of five engineers through a zero-downtime migration of the billing platform to a fault-tolerant event-driven architecture",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
            {
              id: "00000000-0000-4000-8000-000000000012",
              source_bullet_id: "00000000-0000-4000-8000-000000000112",
              text: "Reduced on-call pages by 40% with better alerts",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
          ],
        },
        {
          experience_id: "00000000-0000-4000-8000-000000000003",
          variant_id: "00000000-0000-4000-8000-000000000004",
          title: "Engineer",
          company: "Difference Works",
          location: "Cambridge",
          dates: "2018 - 2021",
          bullets: [
            {
              id: "00000000-0000-4000-8000-000000000013",
              source_bullet_id: "00000000-0000-4000-8000-000000000113",
              text: "Built the first version of the reporting service used by 30 internal teams",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
            {
              id: "00000000-0000-4000-8000-000000000014",
              source_bullet_id: "00000000-0000-4000-8000-000000000114",
              text: "Wrote the test suite that caught regressions before every release",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
          ],
        },
      ],
    },
    {
      key: "projects",
      items: [
        {
          project_id: "00000000-0000-4000-8000-000000000005",
          name: "Notes Compiler",
          url: "https://example.com/notes",
          date: "2023",
          bullets: [
            {
              id: "00000000-0000-4000-8000-000000000015",
              source_bullet_id: "00000000-0000-4000-8000-000000000115",
              text: "Open-source tool that turns plain notes into typeset documents",
              stretched_terms: [],
              covered_keywords: [],
              locked: false,
            },
          ],
        },
      ],
    },
    {
      key: "education",
      items: [
        {
          education_id: "00000000-0000-4000-8000-000000000006",
          institution: "MIT",
          degree: "BS",
          field: "Mathematics",
          location: "Cambridge",
          dates: "2014 - 2018",
          details: [],
        },
      ],
    },
    {
      key: "skills",
      items: [
        {
          categories: [
            {
              name: "Languages",
              skills: [
                { name: "Python", stretched: false },
                { name: "TypeScript", stretched: false },
              ],
            },
            {
              name: "Tools",
              skills: [
                { name: "Git", stretched: false },
                { name: "Docker", stretched: false },
              ],
            },
          ],
        },
      ],
    },
  ],
};

export const FIRST_BULLET_ID = "00000000-0000-4000-8000-000000000010";
