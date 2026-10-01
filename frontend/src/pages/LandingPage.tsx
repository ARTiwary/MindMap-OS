import { Link } from "react-router-dom";
import { Brain, GitBranch, Search, Sparkles, ArrowRight } from "lucide-react";

const FEATURES = [
  {
    icon: GitBranch,
    title: "Connect everything",
    body: "Draw explicit relationships between ideas, projects, and references — requires, inspires, contradicts, supports.",
  },
  {
    icon: Search,
    title: "Find it instantly",
    body: "Full-text search across titles, notes, and resources, so nothing you've captured is ever really lost.",
  },
  {
    icon: Sparkles,
    title: "Surface what's missing",
    body: "Rule-based suggestions flag nodes you keep working with side by side but haven't formally connected yet.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <Brain size={22} className="text-accent" />
          <span className="font-display text-lg">MindMap OS</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link to="/login" className="text-white/70 hover:text-white transition-colors px-3 py-2">
            Log in
          </Link>
          <Link
            to="/register"
            className="bg-accent text-black font-medium px-4 py-2 rounded-lg hover:bg-accent-soft transition-colors"
          >
            Get started
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto text-center px-6 pt-20 pb-24">
        <h1 className="font-display text-5xl sm:text-6xl leading-[1.1] mb-6">
          Your knowledge.
          <br />
          <span className="text-accent">Connected.</span>
        </h1>
        <p className="text-white/50 text-lg max-w-xl mx-auto mb-10">
          Capture ideas, connect concepts, and see your knowledge as a living graph — not another
          folder of notes you'll never reopen.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            to="/register"
            className="bg-accent text-black font-medium px-6 py-3 rounded-lg hover:bg-accent-soft transition-colors inline-flex items-center gap-2"
          >
            Start your graph <ArrowRight size={16} />
          </Link>
          <Link
            to="/login"
            className="border border-border px-6 py-3 rounded-lg hover:border-accent/50 transition-colors"
          >
            I have an account
          </Link>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 pb-10">
        <div className="card p-4 aspect-[16/7] flex items-center justify-center overflow-hidden relative">
          <GraphPreview />
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-24 grid grid-cols-1 md:grid-cols-3 gap-6">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <div key={title} className="card p-6">
            <Icon size={20} className="text-accent mb-4" />
            <h3 className="font-display text-lg mb-2">{title}</h3>
            <p className="text-sm text-white/50">{body}</p>
          </div>
        ))}
      </section>

      <footer className="max-w-6xl mx-auto px-6 py-10 text-center text-xs text-white/30 border-t border-border">
        MindMap OS — a personal knowledge graph.
      </footer>
    </div>
  );
}

/** A small static SVG preview of a mind-map graph — no runtime cost, sets the tone immediately. */
function GraphPreview() {
  const nodes = [
    { x: 250, y: 90, label: "Python", color: "#7C8CFF" },
    { x: 110, y: 170, label: "FastAPI", color: "#5CC2F2" },
    { x: 250, y: 220, label: "AsyncIO", color: "#5CD6C0" },
    { x: 400, y: 170, label: "SQLAlchemy", color: "#F5B95C" },
    { x: 480, y: 60, label: "PostgreSQL", color: "#B98CE8" },
    { x: 60, y: 60, label: "Testing", color: "#F27878" },
  ];
  const edges = [
    [0, 1], [0, 2], [0, 3], [1, 5], [3, 4],
  ];
  return (
    <svg viewBox="0 0 550 280" className="w-full h-full">
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
          stroke="currentColor" className="text-white/10" strokeWidth={1.5}
        />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle cx={n.x} cy={n.y} r={26} fill={`${n.color}22`} stroke={n.color} strokeWidth={1.5} />
          <text x={n.x} y={n.y + 42} textAnchor="middle" fontSize={12} fill="currentColor" className="text-white/60">
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}
