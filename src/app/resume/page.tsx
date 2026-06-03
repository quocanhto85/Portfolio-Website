import Link from "next/link";
import { getResume } from "@/lib/content";

export const dynamic = "force-dynamic";

function Section({
  title,
  children,
}: Readonly<{
  title: string;
  children: React.ReactNode;
}>) {
  return (
    <section className="space-y-3 border-t border-cyan-300/20 pt-5">
      <h2 className="flex items-center gap-2 text-xl font-semibold text-cyan-50">
        <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(57,243,255,0.9)]" />
        {title}
      </h2>
      {children}
    </section>
  );
}

function BulletList({ items }: Readonly<{ items: string[] }>) {
  return (
    <ul className="list-disc space-y-2 pl-5 text-cyan-100/85 marker:text-cyan-300">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export default async function ResumePage() {
  const { personal, skills, education, certifications, experience, projects } =
    await getResume();
  const contactLinks = personal.contact;
  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-900 px-6 py-6 text-slate-100 [background:radial-gradient(circle_at_0%_0%,rgba(118,67,227,0.20),transparent_38%),radial-gradient(circle_at_100%_0%,rgba(30,196,255,0.18),transparent_34%),linear-gradient(180deg,#0a0f1f_0%,#06070d_58%,#04050a_100%)] sm:py-10">
      <div className="pointer-events-none absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:22px_22px]" />
      <div className="relative z-10 mx-auto w-full max-w-5xl">
        <div className="mb-8 flex justify-center">
          <Link
            href="/"
            className="rounded-lg border border-cyan-300/55 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-2 text-sm font-medium text-cyan-100 shadow-[0_0_14px_rgba(69,229,255,0.12)] transition hover:-translate-y-0.5 hover:border-cyan-200 hover:bg-cyan-300/10 hover:text-cyan-50 hover:shadow-[0_0_18px_rgba(69,229,255,0.28)]"
          >
            &larr; Back to Home
          </Link>
        </div>

        <article className="relative overflow-hidden rounded-2xl border border-cyan-300/50 bg-[linear-gradient(145deg,rgba(0,30,38,0.76),rgba(0,8,18,0.93))] p-5 leading-7 text-cyan-100/85 shadow-[0_0_0_1px_rgba(34,220,255,0.14),0_0_28px_rgba(0,196,255,0.15),inset_0_0_32px_rgba(0,149,255,0.08)] sm:p-8">
          <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:18px_18px]" />
          <div className="relative z-10 space-y-7">
            <header className="space-y-4 border-b border-cyan-300/30 pb-5">
              <div className="flex items-center gap-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-cyan-300 shadow-[0_0_12px_rgba(57,243,255,0.9)]" />
                <p className="text-xs tracking-[0.18em] text-cyan-100">
                  RESUME DOSSIER
                </p>
                <span className="ml-auto text-[10px] tracking-[0.14em] text-emerald-300">
                  ONLINE
                </span>
              </div>
              <h1 className="text-3xl font-semibold tracking-tight text-cyan-50">
                {personal.name}
              </h1>
              <div className="flex flex-wrap gap-x-2 gap-y-1 text-sm text-cyan-100/70">
                {contactLinks.map((link, index) => (
                  <span key={link.label}>
                    <a
                      href={link.href}
                      className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                      target={
                        link.href.startsWith("http") ? "_blank" : undefined
                      }
                      rel={
                        link.href.startsWith("http") ? "noreferrer" : undefined
                      }
                    >
                      {link.label}
                    </a>
                    {index < contactLinks.length - 1 ? (
                      <span className="pl-2 text-cyan-300/35">|</span>
                    ) : null}
                  </span>
                ))}
              </div>
            </header>

            <Section title="Summary">
              <p className="text-cyan-100/85">{personal.summary}</p>
            </Section>

            <Section title="Skills">
              <ul className="list-disc space-y-1.5 pl-5 marker:text-cyan-300">
                {skills.map((skill) => (
                  <li key={skill.label}>
                    <span className="font-semibold text-cyan-50">
                      {skill.label}:
                    </span>{" "}
                    {skill.value}
                  </li>
                ))}
              </ul>
            </Section>

            <Section title="Education">
              <div className="space-y-4">
                {education.map((item) => (
                  <div key={item.school} className="space-y-1">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                      <h3 className="font-semibold text-cyan-50">
                        {item.school}
                      </h3>
                      <p className="text-sm text-cyan-200/60">{item.location}</p>
                    </div>
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                      <p>
                        {item.degree} | {item.details}
                      </p>
                      <p className="text-sm text-cyan-200/60">{item.dates}</p>
                    </div>
                    {item.reference ? (
                      <ul className="list-disc pt-1 pl-5 text-cyan-100/80 marker:text-cyan-300">
                        <li>
                          Reference -{" "}
                          <a
                            href={item.reference.profileUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                          >
                            {item.reference.name}
                          </a>{" "}
                          [
                          <a
                            href={`mailto:${item.reference.email}`}
                            className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                          >
                            {item.reference.role}
                          </a>
                          ]
                        </li>
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Professional Experience">
              <div className="space-y-6">
                {experience.map((job) => (
                  <div key={`${job.company}-${job.role}`} className="space-y-3">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                      <h3 className="font-semibold text-cyan-50">
                        <a
                          href={job.companyUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="underline underline-offset-4 transition hover:text-cyan-200"
                        >
                          {job.company}
                        </a>
                      </h3>
                      <p className="text-sm text-cyan-200/60">{job.location}</p>
                    </div>
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                      <p className="font-semibold text-cyan-100">{job.role}</p>
                      <p className="text-sm text-cyan-200/60">{job.dates}</p>
                    </div>
                    <BulletList items={job.bullets} />
                    {job.reference ? (
                      <ul className="list-disc pl-5 text-cyan-100/85 marker:text-cyan-300">
                        <li>
                          Reference -{" "}
                          <a
                            href={job.reference.profileUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                          >
                            {job.reference.name}
                          </a>{" "}
                          [
                          <a
                            href={`mailto:${job.reference.email}`}
                            className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                          >
                            {job.reference.role}
                          </a>
                          ]
                        </li>
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Personal Projects">
              <div className="space-y-6">
                {projects.map((project) => (
                  <div key={project.name} className="space-y-3">
                    <h3 className="font-semibold text-cyan-50">
                      {project.name}
                    </h3>
                    <BulletList items={project.bullets} />
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Courses & Certifications">
              <ul className="list-disc space-y-2 pl-5 marker:text-cyan-300">
                {certifications.map((certification) => (
                  <li key={certification.title}>
                    <a
                      href={certification.href}
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyan-200 underline underline-offset-4 transition hover:text-cyan-50"
                  >
                    {certification.title}
                  </a>{" "}
                  |{" "}
                  <span className="text-cyan-200/60">
                    {certification.issued}
                  </span>
                </li>
              ))}
            </ul>
            </Section>
          </div>
        </article>
      </div>
    </main>
  );
}
