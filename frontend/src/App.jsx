import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";

export default function App() {
  const [view, setView] = useState("home");

  return (
    <div className="h-screen w-full bg-white overflow-hidden selection:bg-blue-100 selection:text-blue-900" style={{ fontFamily: '"Inter", sans-serif' }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600;1,700&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap');
        @keyframes shimmer { 100% { transform: translateX(100%); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-up { animation: fadeInUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards; }
        :root {
          --doc-panel-bg: #f8fbff;
          --doc-panel-surface: #ffffff;
          --doc-panel-muted: #eef4fb;
          --doc-panel-pill: #ffffff;
          --doc-panel-pill-text: #557089;
          --doc-panel-border: rgba(24, 95, 165, 0.14);
          --doc-panel-foreground: #13283f;
          --doc-panel-subtle: #68819b;
          --doc-panel-mono: #587391;
          --doc-panel-overlay: rgba(248, 251, 255, 0.78);
        }
        .dark {
          --doc-panel-bg: #0d1724;
          --doc-panel-surface: #122033;
          --doc-panel-muted: #162739;
          --doc-panel-pill: #122033;
          --doc-panel-pill-text: #a7bfd8;
          --doc-panel-border: rgba(117, 157, 199, 0.2);
          --doc-panel-foreground: #edf4fb;
          --doc-panel-subtle: #9ab1c8;
          --doc-panel-mono: #8ca8c4;
          --doc-panel-overlay: rgba(13, 23, 36, 0.76);
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
        ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
      
      <AnimatePresence mode="wait" initial={false}>
        {view === "home" ? (
          <Home key="home" onEnter={() => setView("dashboard")} />
        ) : view === "about" ? (
          <About key="about" onBack={() => setView("dashboard")} />
        ) : (
          <Dashboard key="dashboard" onBack={() => setView("home")} onAbout={() => setView("about")} />
        )}
      </AnimatePresence>
    </div>
  );
}
