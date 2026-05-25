export type ContentBlock =
  | { type: "paragraph"; text: string }
  | { type: "heading"; text: string }
  | { type: "list"; items: string[] };

export type Project = {
  slug: string;
  title: string;
  date: string;
  description: string;
  imageSrc: string;
  tags: string[];
  githubUrl?: string;
  content: ContentBlock[];
};

export const projects: Project[] = [
  {
    slug: "visual-slam-autonomous-tram",
    title: "Futuristic Autonomous Tram Technology in Smart Cities",
    date: "2025-12-07",
    description:
      "Object-based Visual SLAM system developed for addressing the complexity introduced by dynamic obstacles (e.g., vehicles, pedestrians) along with infrastructure components (e.g., traffic lights, stations).",
    imageSrc: "/images/tram.png",
    tags: [
      "AI",
      "Computer Vision",
      "Robotics",
      "Visual SLAM",
      "ORB-SLAM3",
      "ByteTrack",
      "CubeSLAM",
      "Docker",
    ],
    githubUrl: "https://github.com/quocanhto85/Object-based-Visual-SLAM",
    content: [
      {
        type: "paragraph",
        text: "Finally wrapped up my Master's capstone project, and honestly, it's been quite a ride. For the past several months, I've been deep in the world of Visual SLAM from zero, trying to figure out how we can mimic autonomous vehicles actually work in busy urban environments. It turned out to be a lot tougher than I expected.",
      },
      {
        type: "paragraph",
        text: "The core question I wanted to tackle was pretty straightforward. How do we help a vehicle \"see\" and understand dynamic urban scenes, cars cutting across, cyclists appearing out of nowhere, pedestrians doing unpredictable things, while simultaneously building a map and knowing where it is?",
      },
      { type: "heading", text: "So what did I actually build?" },
      {
        type: "paragraph",
        text: "I put together a full pipeline that combines:",
      },
      {
        type: "list",
        items: [
          "✅ YOLOv8 for detecting objects in real-time",
          "✅ ByteTrack to keep consistent IDs on those objects across frames (no more treating the same car as 10 different cars)",
          "✅ CubeSLAM-style 3D bounding box reconstruction",
          "✅ All of this integrated into ORB-SLAM3 running in monocular mode",
        ],
      },
      {
        type: "paragraph",
        text: "The whole thing runs on my M1 MacBook Pro with 16GB RAM inside a Docker container. Yes, I had to containerise everything because the Pangolin visualisation library often fails on macOS.",
      },
      { type: "heading", text: "What's in the video?" },
      {
        type: "paragraph",
        text: "There are 2 parts in the video. First one (00:00 - 00:24) shows the system running on KITTI odometry sequence 08 with ByteTrack doing its thing, you can see how objects maintain their IDs as the camera moves through the scene. Second part (00:24 - 00:59) is what I'm most excited about: real-world testing on Adelaide suburban streets. Same pipeline, completely different environment.",
      },
      { type: "heading", text: "What's actually new here?" },
      {
        type: "paragraph",
        text: "Most existing work either focuses purely on feature-based or direct approaches, and typically evaluates on a single dataset. I trained on BDD100K and tested on KITTI to see how well the model generalises across different driving scenarios. That cross-dataset evaluation combined with persistent 3D object tracking is something I haven't seen done quite this way before.",
      },
      { type: "heading", text: "But let's be real about the limitations." },
      {
        type: "paragraph",
        text: "Monocular vision is hard. My APE sits around 61-64 metres mean error, which tells you everything about the inherent scale ambiguity problem. And the detector still makes some FPs, in the Adelaide portion, there's a moment where traffic signs were misclassified as cyclists. These edge cases remind me there's still plenty of work ahead.",
      },
      { type: "heading", text: "What's next?" },
      {
        type: "paragraph",
        text: "I'm looking at incorporating semantic segmentation and possibly RANSAC filtering to clean things up. Maybe even some reinforcement learning down the line. I also want to leverage SOTA object detector model such as YOLO26 (released in September 2025) to increase the robustness of the system.",
      },
      {
        type: "paragraph",
        text: "None of this would have been possible without the guidance of my supervisor, Dr Mehdi Hosseinzadeh. I deeply appreciate him for his indispensable guidance and support throughout this research journey.",
      },
    ],
  },
];

export function getProjectBySlug(slug: string): Project | undefined {
  return projects.find((p) => p.slug === slug);
}
