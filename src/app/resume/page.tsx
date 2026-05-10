import Link from "next/link";

const contactLinks = [
  {
    label: "Adelaide, South Australia 5037",
    href: "https://www.google.com/maps/search/?api=1&query=Adelaide%2C%20South%20Australia%205037",
  },
  { label: "+61 411 940 300", href: "tel:+61411940300" },
  { label: "quocanhtophuong@gmail.com", href: "mailto:quocanhtophuong@gmail.com" },
  {
    label: "LinkedIn",
    href: "https://www.linkedin.com/in/quoc-anh-to-79024b148/",
  },
  { label: "GitHub", href: "https://github.com/quocanhto85" },
];

const skills = [
  {
    label: "AI Engineering",
    value:
      "Computer Vision (CV), YOLO, Visual SLAM, ORB-SLAM3, Large Language Models (LLM), Retrieval-Augmented Generation (RAG), LangChain, Prompt Engineering, Word Embeddings, Vector Databases",
  },
  {
    label: "Data Science",
    value:
      "Python, SQL, NumPy, Pandas, Matplotlib, Seaborn, Scikit-Learn, TensorFlow, PyTorch, OpenCV, R",
  },
  {
    label: "Database",
    value:
      "Oracle Database, WebLogic Server, Toad, MongoDB, MongoDB Realm, PostgreSQL",
  },
  {
    label: "Cloud",
    value:
      "AWS (ECS/Fargate, API Gateway, RDS/PostgreSQL, S3, IAM, CloudWatch, ALB, WAF), Azure DevOps",
  },
  {
    label: "DevOps & Engineering Practices",
    value:
      "Agile/Scrum, SDLC, CI/CD, GitHub Actions, Git, SVN, Jenkins, Docker, Kubernetes, Microservices, Privileged Identity Management",
  },
  {
    label: "Web & Mobile Development",
    value:
      "Python, FastAPI, Django, Node.js, Express.js, TypeScript, JavaScript, ReactJs, Next.js, React Native, Redux, Angular, Java EE 8, Spring Boot, ASP.NET, RESTful APIs, HTML, CSS, TailwindCSS, Bootstrap",
  },
  {
    label: "Enterprise Platforms",
    value: "Salesforce (Apex, SOQL, Lightning Web Components)",
  },
];

const education = [
  {
    school: "The University of Adelaide",
    location: "Adelaide, South Australia",
    degree: "Master of Artificial Intelligence & Machine Learning",
    details: "GPA: 6.67/7",
    dates: "2024 - 2025",
    reference: {
      name: "Dr. Mehdi Hosseinzadeh",
      profileUrl:
        "https://scholar.google.com/citations?user=HPrbbiIAAAAJ&hl=en",
      role: "Capstone Project Supervisor",
      email: "mehdi.hosseinzadeh@adelaide.edu.au",
    },
  },
  {
    school: "Hanoi University of Science and Technology",
    location: "Hanoi, Vietnam",
    degree: "Bachelor of Computer Sciences",
    details: "GPA: A",
    dates: "2016 - 2020",
    reference: {
      name: "Assoc. Prof. Cao Tuan Dung",
      profileUrl:
        "https://soict.hust.edu.vn/en/assoc-prof-cao-tuan-dung.html",
      role: "Capstone Project Supervisor",
      email: "dung.caotuan@hust.edu.vn",
    },
  },
];

const certifications = [
  {
    title: "Machine Learning by Stanford University",
    issued: "Issued Feb 2021",
    href: "https://www.coursera.org/account/accomplishments/verify/3K5CL5UB6MGF",
  },
  {
    title: "Foundations: Data, Data, Everywhere",
    issued: "Issued Jun 2023",
    href: "https://www.coursera.org/account/accomplishments/certificate/HB8PD6XNLN7N",
  },
  {
    title: "Introduction to the Internet of Things and Embedded Systems",
    issued: "Issued Nov 2020",
    href: "https://www.coursera.org/account/accomplishments/certificate/FU2RTGWWQBGW",
  },
];

const experience = [
  {
    company: "Quantum Savvy Pty Ltd",
    companyUrl: "https://savvy.com.au/",
    location: "Adelaide, South Australia",
    role: "AI Software Engineer (Full-time)",
    dates: "Jan 2026 - Apr 2026",
    bullets: [
      "Architected and developed an AI-powered Knowledge Assistant for asset finance brokers using a RAG pipeline, reducing lender policy query resolution from 15-30 minutes to under 30 seconds; project reached MVP-ready status at departure.",
      "Delivered full-stack Salesforce (AFOS) development across CRM workflows, spanning automated broker notifications, duplicate lead detection, DOF calculation logic, and a custom bulk record transfer tool.",
      "Tools/Skills: LLM, RAG, LangChain, Vector Databases, FastAPI, Python, Prompt Engineering, Word Embeddings, SOQL, Apex, Lightning Web Components, Agile/Scrum.",
    ],
    reference: {
      name: "Bill Tsouvalas",
      profileUrl: "https://www.linkedin.com/in/bill-tsouvalas-bba93653/",
      role: "Managing Director",
      email: "billt@savvy.com.au",
    },
  },
  {
    company: "SPOTFAKE.AI (now LoopSoup AI)",
    companyUrl: "https://loopsoup.ai/",
    location: "Adelaide, South Australia",
    role: "Full Stack Developer (Internship)",
    dates: "Feb 2025 - Apr 2025",
    bullets: [
      "Addressed technical debt by testing and validating OCR APIs using Postman, restructuring project source code for improved maintainability, and managing application lifecycle including port management and status persistence.",
      "Developed significant frontend and backend features including profile management, logout flows, image/audio detail pages, and database CRUD operations.",
      "Tools/Skills: Next.js, Django, Python, Optical Character Recognition (OCR), RESTful APIs.",
    ],
    reference: {
      name: "Ankit Yadav",
      profileUrl: "https://www.linkedin.com/in/ankityadav008/",
      role: "CTO",
      email: "ankit.yadav@adelaide.edu.au",
    },
  },
  {
    company: "EVN (Vietnam Electricity)",
    companyUrl: "https://en.evn.com.vn/",
    location: "Hanoi, Vietnam",
    role: "Software Engineer (Full-time)",
    dates: "Mar 2021 - Dec 2023",
    bullets: [
      "Modernised and enhanced the electricity Customer Management Information System (CMIS) 4.0 serving nearly 30M customers nationwide, including households and enterprises, across 1,200+ operational units in Vietnam.",
      "Led a team of 6 engineers to deploy mobile solutions across 5+ provinces in northern Vietnam as technical lead for the CMIS Mobile project.",
      "Maintained and enhanced the EVN Gateway system, ensuring secure API interactions for customer authentication and data access with the National Population Database under Vietnam's Ministry of Public Security.",
      "Delivered high-performing software solutions scaling to handle 1M+ service requests annually, ensuring compliance with national data security standards.",
      "Tools/Skills: Angular, React Native, TypeScript, Java EE 8, ASP.NET, SQL, Oracle Database, MongoDB Realm, WebLogic Server, Git, Jenkins, SVN, Microservices, Azure DevOps, SDLC, Privileged Identity Management.",
    ],
  },
  {
    company: "FTECH CO., LTD",
    companyUrl: "https://ftech.ai/en",
    location: "Hanoi, Vietnam",
    role: "Front-end Developer (Part-time)",
    dates: "Jun 2019 - Dec 2020",
    bullets: [
      "Collaborated with a team of 7 engineers to develop an online Learning Management System (Eclazz), serving 1M+ learning materials for over 10K students and trusted by 1,340+ teachers across 320+ organisations.",
      "Designed and implemented a Content Management System for a gaming portal, improving content delivery workflows.",
      "Tools/Skills: HTML, CSS, Bootstrap, JavaScript, ReactJs, Redux, Node.js, Express.js, RESTful APIs, MongoDB, CI/CD, Docker, Kubernetes.",
    ],
  },
];

const projects = [
  {
    name: "Object-Based Visual SLAM for Urban Tram Navigation",
    bullets: [
      "Developed an end-to-end Visual SLAM pipeline integrating YOLOv8 object detection, ByteTrack multi-object tracking, and CubeSLAM-based 3D cuboid reconstruction into ORB-SLAM3, achieving 0.52 mean 3D IoU and 65% precision on KITTI odometry sequences.",
      "Demonstrated cross-dataset generalisation by training on BDD100K (100K images) and evaluating on KITTI; ByteTrack integration reduced redundant map entities by 81.2% through persistent object identity tracking.",
      "Containerised the ORB-SLAM3 development environment using Docker with X11 forwarding, enabling real-time 3D visualisation and deployment on Adelaide urban footage.",
    ],
  },
  {
    name: "Hybrid Recommender System for Grocery Retail",
    bullets: [
      "Built a hybrid recommender combining FP-Growth frequent pattern mining and item-based collaborative filtering (KNN, cosine similarity) with recency-aware personalisation on around 38,600 grocery transactions.",
      "Hybrid model outperformed standalone collaborative filtering across key metrics: Precision@5 (0.2040 vs. 0.2014), Recall@5 (0.1911 vs. 0.1886), and Hit Rate@5 (0.6529 vs. 0.6476), while addressing cold start and 98.86% matrix sparsity via frequent-itemset fallback and eager pre-computation for real-time inference.",
    ],
  },
  {
    name: "RNNs for Stock Price Prediction",
    bullets: [
      "Designed and optimised a Recurrent Neural Network (RNN) model using Stacked LSTM architectures in Python with TensorFlow and Keras, achieving a 47% reduction in MSE for stock price forecasting vs. traditional methods.",
    ],
  },
  {
    name: "Diabetes Prediction using Perceptron",
    bullets: [
      "Optimised a Perceptron algorithm for diabetes prediction, achieving 74.68% accuracy on the Pima Indians Diabetes dataset through hyperparameter tuning, demonstrating mastery of supervised learning fundamentals.",
    ],
  },
];

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

export default function ResumePage() {
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
                (Bruce) Phuong Quoc Anh To
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
              <p className="text-cyan-100/85">
                Results-driven AI Software Engineer with 4+ years of full-stack
                engineering experience and a Master&apos;s in Artificial
                Intelligence & Machine Learning from the University of Adelaide
                (GPA 6.67/7). Proven ability to architect and ship AI-powered
                products, including RAG pipelines, LLM integrations, and computer
                vision systems, while maintaining engineering rigour across
                backend, cloud, and DevOps. Experienced in scaling solutions from
                prototype to production in fast-paced, cross-functional Agile
                teams.
              </p>
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
