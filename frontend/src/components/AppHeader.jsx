import { GraduationCap } from "lucide-react";

export default function AppHeader() {
  return (
    <header className="border-b border-blue-100 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex h-full w-full max-w-[1680px] items-center justify-between px-4 sm:px-5 xl:px-6">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-blue-600 shadow-sm">
          <GraduationCap className="h-5 w-5" />
        </div>
        <div className="text-[1.15rem] font-bold text-slate-900 sm:text-[1.35rem]" style={{ fontFamily: '"Playfair Display", serif' }}>
          Question Paper Generator  
        </div>
      </div>

      <div className="hidden items-center gap-5 text-sm text-blue-600/80 md:flex">
        <span className="cursor-default">Paper Studio</span>
        <span className="cursor-default">Academic Output</span>
      </div>
      </div>
    </header>
  );
}
