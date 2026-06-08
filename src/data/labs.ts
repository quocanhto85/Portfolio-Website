export type LabStatus = "operational" | "prototype" | "provisioning";

export interface Lab {
  id: string;
  slug: string;
  title: string;
  tagline: string;
  status: LabStatus;
  stack: string[];
  href: string | null;
}

export const labs: Lab[] = [
  {
    id: "LAB-001",
    slug: "pomodoro",
    title: "Pomodoro Engine",
    tagline:
      "A Pomodoro-inspired focus timer with structured work/break cycles and progress tracking, built to boost productivity.",
    status: "operational",
    stack: ["Next.js", "Redux", "Socket.io", "MongoDB"],
    href: "https://pomodoro-green-chi.vercel.app/",
  },
];
