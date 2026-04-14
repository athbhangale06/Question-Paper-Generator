import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Sparkles, Target, Settings2, FileText, CheckCircle2 } from "lucide-react";

const pageVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.3 } },
};

const promptExamples = [
  {
    title: "Structure & Marking",
    description: "Define exact sections and their weights for precise formatting.",
    prompt: "The question paper should contain sections like A, B, and C, each of 10 marks, for a total of 30 marks.",
    icon: FileText
  },
  {
    title: "Difficulty & Cognitive Level",
    description: "Control the analytical depth using Bloom's Taxonomy keywords.",
    prompt: "Generate an advanced level paper focusing on \"Evaluate\" and \"Analyze\" questions. Avoid simple recall questions.",
    icon: Target
  },
  {
    title: "Specific Topics & Inclusions",
    description: "Constrain the AI to specific chapters or concepts.",
    prompt: "Focus exclusively on Thermodynamics and Kinematics. Ensure at least two numerical problems are included in every section.",
    icon: BookOpen
  },
  {
    title: "Format & Question Types",
    description: "Ask for a mix of MCQs, Short Answers, and Long Essays.",
    prompt: "Include 10 Multiple Choice Questions, 5 Short Answer Questions, and 2 Long Essay Questions requiring diagrams.",
    icon: Settings2
  },
  {
    title: "Theme & Contextual Scenario",
    description: "Make questions scenario-based to test practical application.",
    prompt: "Frame all the short answer questions around real-world contextual scenarios encountered in modern engineering.",
    icon: Sparkles
  }
];

export default function About({ onBack }) {
  return (
    <motion.main
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="relative z-10 h-full w-full bg-[#fafafc] selection:bg-blue-100 selection:text-blue-900 overflow-y-auto no-scrollbar"
      style={{ fontFamily: '"Inter", sans-serif' }}
    >
      <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-blue-100 bg-white/80 px-6 sm:px-12 backdrop-blur-md shadow-sm">
        <div className="flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-blue-600" />
          <span className="text-xl font-bold tracking-tight text-slate-800" style={{ fontFamily: '"Playfair Display", serif' }}>
            About Question Paper Generator
          </span>
        </div>
        <button
          onClick={onBack}
          className="group flex items-center gap-2 rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-semibold text-slate-600 shadow-sm transition-all hover:bg-slate-50 hover:text-blue-600"
        >
          <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
          Back to Generator
        </button>
      </header>

      <div className="mx-auto max-w-4xl px-6 py-12 sm:px-12 sm:py-20">
        <div className="text-center mb-16">
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-800 mb-6" style={{ fontFamily: '"Playfair Display", serif' }}>
            Mastering Your Prompts
          </h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto leading-relaxed">
            EduPaper AI uses advanced language models to generate precise academic documents. The more specific you are in your <strong>Custom Prompt</strong> and <strong>Source Material</strong>, the more efficient and tailored the output will be.
          </p>
        </div>

        <div className="space-y-16">
          <section>
            <div className="flex items-center gap-3 mb-8 border-b border-slate-200 pb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                <Target className="h-5 w-5" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800" style={{ fontFamily: '"Playfair Display", serif' }}>
                How to Get Efficient Output
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-2xl border border-emerald-100 bg-emerald-50/50 p-6">
                <h3 className="flex items-center gap-2 text-lg font-bold text-emerald-800 mb-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" /> Do's
                </h3>
                <ul className="space-y-3 text-sm text-emerald-700/80 font-medium">
                  <li>• Upload clear, text-based PDF or DOCX files for context.</li>
                  <li>• Specify exactly how many questions you need.</li>
                  <li>• Define the mark allocation explicitly in the prompt.</li>
                  <li>• Use strict formatting commands (e.g. "Use bullet points").</li>
                </ul>
              </div>
              <div className="rounded-2xl border border-amber-100 bg-amber-50/50 p-6">
                <h3 className="flex items-center gap-2 text-lg font-bold text-amber-800 mb-3">
                  <Settings2 className="h-5 w-5 text-amber-500" /> Tips
                </h3>
                <ul className="space-y-3 text-sm text-amber-700/80 font-medium">
                  <li>• If the first paper isn't perfect, use the variant previews!</li>
                  <li>• Combine multiple constraints into one prompt for maximum control.</li>
                  <li>• Tell the AI the "persona" it should take (e.g., "Act as a strict grading professor").</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <div className="flex items-center gap-3 mb-8 border-b border-slate-200 pb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
                <Sparkles className="h-5 w-5" />
              </div>
              <h2 className="text-2xl font-bold text-slate-800" style={{ fontFamily: '"Playfair Display", serif' }}>
                5 Proven Prompt Examples
              </h2>
            </div>

            <div className="space-y-6">
              {promptExamples.map((example, idx) => {
                const Icon = example.icon;
                return (
                  <div key={idx} className="group flex flex-col sm:flex-row gap-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm transition-all hover:border-blue-300 hover:shadow-md">
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-slate-50 text-slate-400 transition-colors group-hover:bg-blue-600 group-hover:text-white">
                      <Icon className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-slate-800 mb-1">{example.title}</h3>
                      <p className="text-sm font-medium text-slate-500 mb-4">{example.description}</p>
                      <div className="rounded-xl border border-slate-100 bg-slate-50 relative p-4">
                        <span className="absolute -top-2.5 left-4 bg-slate-50 px-2 text-[10px] font-bold uppercase tracking-widest text-slate-400">Example Prompt</span>
                        <p className="text-sm italic leading-relaxed text-slate-700">"{example.prompt}"</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </motion.main>
  );
}
