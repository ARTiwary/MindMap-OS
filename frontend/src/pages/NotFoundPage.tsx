import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center px-6">
      <h1 className="font-display text-6xl text-accent mb-4">404</h1>
      <p className="text-white/50 mb-6">This node doesn't exist in your knowledge graph.</p>
      <Link to="/dashboard" className="text-accent hover:underline text-sm">
        Back to dashboard
      </Link>
    </div>
  );
}
