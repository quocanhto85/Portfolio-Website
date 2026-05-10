import Image from "next/image";

type ProjectCard = {
  title: string;
  date: string;
  description: string;
  imageSrc: string;
  tags: string[];
};

const projects: ProjectCard[] = [
  {
    title: "Futuristic Autonomous Tram Technology in Smart Cities",
    date: "2025-12-07",
    description:
      "Object-based Visual SLAM system developed for addressing the complexity introduced by dynamic obstacles (e.g., vehicles, pedestrians) along with infrastructure components (e.g., traffic lights, stations).",
    imageSrc: "/images/tram.png",
    tags: ["AI", "Computer Vision", "Robotics", "Visual SLAM", "ORB-SLAM3", "ByteTrack", "CubeSLAM", "Docker"],
  }
];

const links = [
  {
    label: "Email",
    value: "channel:01",
    href: "mailto:quocanhtophuong@gmail.com",
  },
  {
    label: "LinkedIn",
    value: "channel:02",
    href: "https://www.linkedin.com/in/quoc-anh-to-79024b148/",
    opensNewTab: true,
  },
  {
    label: "GitHub",
    value: "channel:03",
    href: "https://github.com/quocanhto85",
    opensNewTab: true,
  },
  {
    label: "Resume",
    value: "channel:04",
    href: "/resume",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-batcave px-6 py-10 text-slate-100">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-3">
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">
            🦇 Quoc Anh&apos;s Batcave
          </h1>
          <nav className="relative overflow-hidden rounded-2xl border border-cyan-300/60 bg-[linear-gradient(145deg,rgba(0,30,38,0.8),rgba(0,8,18,0.92))] p-4 shadow-[0_0_0_1px_rgba(34,220,255,0.15),0_0_24px_rgba(0,196,255,0.16),inset_0_0_30px_rgba(0,149,255,0.08)]">
            <div className="pointer-events-none absolute inset-0 opacity-35 [background-image:linear-gradient(rgba(88,251,255,0.09)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.07)_1px,transparent_1px)] [background-size:18px_18px]" />
            <div className="relative z-10 mb-3 flex items-center gap-2.5 border-b border-cyan-300/40 pb-2">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-300 shadow-[0_0_12px_rgba(57,243,255,0.9)]" />
              <p className="text-xs tracking-[0.18em] text-cyan-100">CONTACT CONSOLE</p>
              <span className="ml-auto text-[10px] tracking-[0.14em] text-emerald-300">
                ONLINE
              </span>
            </div>
            <div className="relative z-10 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {links.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target={link.opensNewTab ? "_blank" : undefined}
                  rel={link.opensNewTab ? "noreferrer" : undefined}
                  className="flex items-baseline justify-between gap-2 rounded-lg border border-cyan-300/40 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-3 py-2 text-sm text-cyan-50 transition hover:-translate-y-0.5 hover:border-cyan-200 hover:shadow-[0_0_12px_rgba(69,229,255,0.26)]"
                >
                  <span>{link.label}</span>
                  <span className="text-[10px] tracking-[0.08em] text-cyan-200/80">
                    {link.value}
                  </span>
                </a>
              ))}
            </div>
          </nav>
        </header>

        <div className="relative overflow-hidden rounded-xl border border-cyan-300/50 bg-[linear-gradient(145deg,rgba(0,30,38,0.7),rgba(0,8,18,0.9))] p-3 shadow-[0_0_0_1px_rgba(34,220,255,0.12),0_0_20px_rgba(0,196,255,0.12),inset_0_0_24px_rgba(0,149,255,0.08)]">
          <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:18px_18px]" />
          <input
            aria-label="Search by title, tag or keyword"
            placeholder="Search by title, tag or keyword..."
            className="relative z-10 w-full rounded-lg border border-cyan-300/35 bg-[linear-gradient(180deg,rgba(2,30,45,0.55),rgba(0,10,20,0.72))] px-4 py-3 text-sm text-cyan-50 placeholder:text-cyan-200/45 outline-none transition focus:border-cyan-200 focus:ring-2 focus:ring-cyan-300/25"
          />
        </div>

        <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <article
              key={project.title}
              className="group relative overflow-hidden rounded-2xl border border-cyan-300/45 bg-[linear-gradient(145deg,rgba(0,30,38,0.78),rgba(0,8,18,0.92))] shadow-[0_0_0_1px_rgba(34,220,255,0.12),0_0_24px_rgba(0,196,255,0.14),inset_0_0_30px_rgba(0,149,255,0.07)]"
            >
              <div className="pointer-events-none absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(88,251,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(88,251,255,0.06)_1px,transparent_1px)] [background-size:18px_18px]" />
              <div className="relative h-72 w-full border-b border-cyan-300/25 bg-black/30">
                <Image
                  src={project.imageSrc}
                  alt={project.title}
                  fill
                  className="object-cover"
                />
              </div>
              <div className="relative z-10 space-y-3 p-4">
                <p className="text-xs text-cyan-200/70">{project.date}</p>
                <h2 className="text-lg leading-tight text-cyan-50">
                  {project.title}
                </h2>
                <p className="text-sm text-cyan-100/85">{project.description}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-cyan-300/45 bg-cyan-300/10 px-2.5 py-1 text-xs text-cyan-100"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}
