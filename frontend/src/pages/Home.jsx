import { useState } from "react";
import { ArrowRight, FileText } from "lucide-react";
import { motion } from "framer-motion";

const pageVariants = {
  initial: (direction) => ({ opacity: 0, x: direction > 0 ? 30 : -30 }),
  animate: { opacity: 1, x: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
  exit: (direction) => ({ opacity: 0, x: direction > 0 ? -30 : 30, transition: { duration: 0.3, ease: [0.4, 0, 1, 1] } }),
};

function PulsingLines({ position }) {
  const sentences = position === "top" 
    ? [
        "The theoretical framework delineates the fundamental boundaries.",
        "Quantitative parameters reveal a statistically significant trend.",
        "Historical precedents indicate recurring multifaceted variables.",
        "Abstract structures determine the robustness of the methodology."
      ]
    : [
        "Semantic relationships map the interconnected network dynamics.",
        "A comprehensive literature review exposes crucial academic gaps.",
        "Thermodynamic principles dictate the spontaneous reaction curves.",
        "These stylistic elements amplify the overarching thematic scope."
      ];

  const maskStyle = { 
    maskImage: 'linear-gradient(to right, black 50%, transparent 95%)', 
    WebkitMaskImage: 'linear-gradient(to right, black 50%, transparent 95%)' 
  };

  return (
    <div className={`absolute ${position === "top" ? "top-10" : "bottom-10"} left-12 right-12 space-y-2 pointer-events-none`}>
      {sentences.map((text, i) => (
        <motion.p
           key={i}
           animate={{ opacity: [0.2, 0.6, 0.2] }}
           transition={{ duration: 3 + i * 0.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.4 }}
           className="text-[12px] font-medium leading-relaxed tracking-wide text-slate-500 whitespace-nowrap overflow-hidden italic" 
           style={maskStyle}
        >
          {text}
        </motion.p>
      ))}
    </div>
  );
}

function DocumentEnvelope({ onLaunch }) {
  const [isLaunching, setIsLaunching] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = () => {
    if (isLaunching) return;
    setIsLaunching(true);
    setTimeout(() => {
      onLaunch();
    }, 1200);
  };

  const pages = [
    { rotate: -8, x: -25, y: -90, delay: 0.15 },
    { rotate: 0, x: 0, y: -110, delay: 0 },
    { rotate: 10, x: 25, y: -70, delay: 0.25 },
  ];

  return (
    <div className="relative z-20 flex flex-col items-center justify-center">
      <motion.button
        onClick={handleClick}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
        className="group relative flex flex-col items-center justify-center cursor-pointer focus:outline-none outline-none"
      >
        <div className="relative flex h-40 w-44 items-end justify-center rounded-2xl transition-all hover:scale-105 duration-300">
          
          {/* Back of envelope */}
          <div className="absolute bottom-0 h-[85%] w-full rounded-2xl bg-[#0f3d7a] shadow-inner" />
          
          {/* Pages */}
          {pages.map((p, i) => (
            <motion.div
              key={i}
              initial={{ y: 0, x: 0, rotate: 0, scale: 0.95 }}
              animate={isLaunching ? { y: p.y, x: p.x, rotate: p.rotate, scale: 1 } : { y: isHovered ? -15 - (i * 5) : 0, rotate: isHovered ? (i - 1) * 3 : 0 }}
              transition={{ duration: isLaunching ? 0.6 : 0.3, ease: "easeOut", delay: isLaunching ? p.delay : 0 }}
              className="absolute bottom-4 h-[80%] w-[85%] rounded-lg bg-white border border-slate-200 shadow-md flex flex-col items-center justify-start p-3 gap-2"
            >
               <div className="h-1.5 w-full bg-slate-200 rounded-full" />
               <div className="h-1.5 w-[75%] self-start bg-slate-200 rounded-full" />
               <div className="h-1.5 w-[90%] bg-slate-100 rounded-full mt-2" />
               <div className="h-1.5 w-full bg-slate-100 rounded-full" />
            </motion.div>
          ))}

          {/* Front slanted envelope piece */}
          <div 
            className="absolute bottom-0 h-[75%] w-full rounded-b-2xl overflow-hidden shadow-[0_-5px_15px_rgba(0,0,0,0.25)]"
            style={{ clipPath: "polygon(0 35%, 100% 0, 100% 100%, 0 100%)" }}
          >
            <div className="absolute inset-0 bg-blue-600 border-t border-blue-400 transition-colors group-hover:bg-blue-500" />
            
            {/* Hover Shine Effect */}
            <motion.div 
              initial={{ x: "-100%" }}
              animate={isHovered ? { x: "200%" } : { x: "-100%" }}
              transition={{ duration: 0.7, ease: "easeInOut" }}
              className="absolute top-0 bottom-0 w-1/2 bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12"
            />
          </div>
          
          {/* File Icon on front */}
          <motion.div 
            animate={isHovered && !isLaunching ? { scale: 1.05 } : { scale: 1 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-6 left-6 h-12 w-12 bg-white rounded-xl flex items-center justify-center text-blue-600 shadow-lg border border-blue-100"
          >
             <FileText className="h-6 w-6" strokeWidth={2.5} />
          </motion.div>
        </div>
        
        <motion.div 
          animate={isLaunching ? { opacity: 0, y: 10, scale: 0.9 } : { opacity: isHovered ? 1 : 0, y: isHovered ? 0 : 5, scale: 1 }}
          transition={{ duration: 0.2 }}
          className="absolute -bottom-16 text-[11px] font-bold uppercase tracking-widest text-white rounded-full bg-slate-900 px-5 py-2.5 shadow-xl backdrop-blur-md"
        >
          {isLaunching ? "Generating..." : "Launch App"}
        </motion.div>
      </motion.button>
    </div>
  );
}

export default function Home({ onEnter }) {
  return (
    <motion.main
      custom={1}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="relative z-10 min-h-screen w-full bg-white selection:bg-blue-100 selection:text-blue-900"
    >
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[45%_55%] xl:grid-cols-[40%_60%]">
        {/* Left Column */}
        <section className="relative z-20 flex flex-col justify-between px-8 py-6 lg:px-12 xl:px-20 bg-white shrink-0 shadow-[20px_0_60px_-15px_rgba(0,0,0,0.05)] overflow-y-auto">
          <header className="flex items-center gap-3 shrink-0">
             <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-blue-50 shadow-md border border-blue-100/50">
                <img src="/appLogo.png" alt="App Logo" className="h-[120%] w-[120%] object-cover" />
             </div>
             <div className="text-sm font-bold uppercase tracking-[0.2em] text-slate-800">
               EDUPAPER AI
             </div>
          </header>

          <div className="my-auto w-full py-8">
            <h1 className="text-[clamp(2.75rem,4vw,4.5rem)] font-bold text-slate-800 leading-[1.1]" style={{ fontFamily: '"Playfair Display", serif', letterSpacing: '-0.02em' }}>
              Convert Notes Into Elegant Question Papers<span className="text-blue-500">.</span>
            </h1>
            
            <p className="mt-4 text-base lg:text-lg font-medium leading-relaxed text-slate-500 max-w-sm">
              Upload curriculum files, tailor your prompt requirements, and generate a perfectly formatted academic paper in seconds.
            </p>

            <div className="mt-8">
              <button
                type="button"
                onClick={onEnter}
                className="group relative inline-flex items-center gap-4 rounded-full bg-blue-600 px-8 py-4 text-sm font-bold tracking-wide text-white shadow-[0_12px_30px_rgba(37,99,235,0.2)] transition-all hover:bg-blue-700 hover:-translate-y-1 active:translate-y-0"
              >
                OPEN DASHBOARD
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </button>
            </div>
          </div>

          <footer className="text-[10px] shrink-0 font-bold uppercase tracking-[0.2em] text-slate-400">
             Question Paper Generator • 2026
          </footer>
        </section>

        {/* Right Column - Word Doc representation */}
        <section className="relative z-10 hidden w-full overflow-hidden bg-slate-50 lg:block">
           <div className="absolute inset-0 pointer-events-none z-0">
             <div className="absolute -left-[10%] -top-[10%] h-[60%] w-[50%] rounded-full bg-blue-200/40 blur-[120px]" />
             <div className="absolute right-[0%] bottom-[-10%] h-[70%] w-[60%] rounded-full bg-sky-200/40 blur-[100px]" />
           </div>

           <div className="absolute inset-0 flex items-center justify-center p-12 overflow-hidden z-10">
             <div className="relative w-full max-w-lg aspect-[1/1.3] bg-white rounded-xl shadow-[0_30px_80px_-15px_rgba(0,0,0,0.15)] border border-slate-200 p-10 flex flex-col items-center justify-center overflow-hidden">
                <PulsingLines position="top" />
                <PulsingLines position="bottom" />

                <DocumentEnvelope onLaunch={onEnter} />
             </div>
           </div>
        </section>
      </div>
    </motion.main>
  );
}
