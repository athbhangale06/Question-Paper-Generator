import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Download, FileText, RefreshCcw, Sparkles } from "lucide-react";

const STATUS_COPY = [
  "Analysing parameters...",
  "Structuring sections...",
  "Tuning details for accurate output...",
  "Finalising document layout...",
];

const formatBytes = (bytes) => {
  if (!bytes || Number.isNaN(bytes)) return "Unknown size";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const createSimulatedFiles = (count) =>
  Array.from({ length: count }, (_, index) => ({
    id: `sim-${count}-${index + 1}`,
    name: count === 1 ? "Physics_Final_Paper.docx" : `Physics_Final_Paper_${index + 1}.docx`,
    sizeBytes: 185000 + index * 42000,
    pageCount: 3 + index,
    dateLabel: new Date().toLocaleDateString(),
    downloadUrl: "",
    previewText: "Simulated document ready for review.",
  }));

function StatusPill({ mode }) {
  const isProcessing = mode === "processing";
  const label = mode === "completed" ? "COMPLETED" : mode === "processing" ? "PROCESSING" : "WAITING";

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-[var(--panel-border)] bg-[var(--panel-pill)] px-3 py-1.5 text-[11px] font-semibold tracking-[0.22em] text-[var(--panel-pill-text)]">
      {isProcessing ? (
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#378ADD] opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#185FA5]" />
        </span>
      ) : (
        <span className={`h-2.5 w-2.5 rounded-full ${mode === "completed" ? "bg-emerald-500" : "bg-slate-400"}`} />
      )}
      <span>{label}</span>
    </div>
  );
}

function WaitingState() {
  return (
    <motion.div
      key="waiting"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.28 }}
      className="flex h-full min-h-[30rem] flex-col items-center justify-center px-6 text-center"
    >
      <div className="flex h-20 w-20 items-center justify-center rounded-[28px] border border-[var(--panel-border)] bg-[var(--panel-muted)] text-[#185FA5]">
        <FileText className="h-10 w-10" strokeWidth={1.7} />
      </div>
      <h2 className="mt-6 text-3xl font-semibold text-[var(--panel-foreground)]">Ready to Generate</h2>
      <p className="mt-3 max-w-md text-sm leading-7 text-[var(--panel-subtle)]">
        Your document output panel is standing by. Provide the generation inputs and begin when you're ready.
      </p>
    </motion.div>
  );
}

function ProcessingState({ progress, messageIndex }) {
  return (
    <motion.div
      key="processing"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.28 }}
      className="flex h-full min-h-[30rem] flex-col items-center justify-center px-6"
    >
      <div className="relative flex h-40 w-40 items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "linear" }}
          className="absolute h-24 w-24 rounded-full border-[5px] border-[#378ADD]/20 border-t-[#185FA5] border-r-[#378ADD]"
        />
        <div className="absolute flex items-center gap-2">
          {[0, 1, 2].map((index) => (
            <motion.span
              key={index}
              animate={{
                scale: [0.9, 1.35, 0.9],
                y: [0, -8, 0],
                opacity: [0.55, 1, 0.55],
              }}
              transition={{
                duration: 1.6,
                repeat: Infinity,
                ease: "easeInOut",
                delay: index * 0.18,
              }}
              className="h-3.5 w-3.5 rounded-full bg-[#378ADD]"
            />
          ))}
        </div>
      </div>

      <div className="mt-8 w-full max-w-md">
        <div className="h-2.5 overflow-hidden rounded-full bg-[var(--panel-muted)]">
          <motion.div
            className="h-full rounded-full bg-[linear-gradient(90deg,#185FA5,#378ADD)]"
            animate={{ width: `${Math.max(progress, 6)}%` }}
            transition={{ ease: "easeOut", duration: 0.25 }}
          />
        </div>
        <div className="mt-6 h-8 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.p
              key={messageIndex}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.3 }}
              className="text-center text-sm text-[var(--panel-subtle)]"
            >
              {STATUS_COPY[messageIndex]}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

function DocumentCard({ file, onDownload, downloading }) {
  return (
    <motion.div
      layout
      whileHover={{ y: -2 }}
      className="group relative overflow-hidden rounded-3xl border border-[var(--panel-border)] bg-[var(--panel-surface)] transition-colors"
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[#378ADD]/20 bg-[#378ADD]/8 text-[#185FA5]">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <p className="font-medium text-[var(--panel-foreground)]">{file.name}</p>
              <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.18em] text-[var(--panel-mono)]" style={{ fontFamily: '"DM Mono", monospace' }}>
                <span>{formatBytes(file.sizeBytes)}</span>
                <span>{file.pageCount} pages</span>
                <span>{file.dateLabel}</span>
              </div>
            </div>
          </div>
          <span className="rounded-full border border-[var(--panel-border)] bg-[var(--panel-muted)] px-2.5 py-1 text-[10px] uppercase tracking-[0.22em] text-[var(--panel-mono)]" style={{ fontFamily: '"DM Mono", monospace' }}>
            .docx
          </span>
        </div>

        <div className="mt-5 flex items-center justify-between gap-4">
          <p className="text-sm text-[var(--panel-subtle)]">Click to download</p>
          <button
            type="button"
            onClick={() => onDownload(file)}
            disabled={downloading}
            className="inline-flex items-center gap-2 rounded-2xl border border-[#378ADD]/20 bg-[#378ADD]/10 px-4 py-2 text-sm font-medium text-[#185FA5] transition-colors hover:bg-[#378ADD]/15 disabled:cursor-wait disabled:opacity-70"
          >
            <Download className="h-4 w-4" />
            <span>{downloading ? "Preparing..." : "Download"}</span>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {downloading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-[var(--panel-overlay)] backdrop-blur-[2px]"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              className="h-10 w-10 rounded-full border-[3px] border-[#378ADD]/25 border-t-[#185FA5]"
            />
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ scaleX: 0 }}
        animate={{ scaleX: downloading ? 1 : 0 }}
        transition={{ duration: downloading ? 1.2 : 0.2, ease: "easeInOut" }}
        className="absolute bottom-0 left-0 h-1 w-full origin-left bg-[linear-gradient(90deg,#185FA5,#378ADD)]"
      />
    </motion.div>
  );
}

function ToastStack({ toasts }) {
  return (
    <div className="pointer-events-none absolute bottom-5 right-5 z-20 flex w-[22rem] max-w-[calc(100%-2rem)] flex-col gap-3">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.28 }}
            className="flex items-center gap-3 rounded-2xl border border-emerald-500/20 bg-emerald-500 px-4 py-3 text-white"
          >
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            <p className="text-sm font-medium">{toast.message}</p>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default function DocumentGenerationPanel({
  status = "waiting",
  files = [],
  onGenerate,
  onReset,
}) {
  const [simulationMode, setSimulationMode] = useState(null);
  const [simulationFiles, setSimulationFiles] = useState([]);
  const [progress, setProgress] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);
  const [downloadingId, setDownloadingId] = useState(null);
  const [toasts, setToasts] = useState([]);
  const progressTimerRef = useRef(null);
  const messageTimerRef = useRef(null);

  const resolvedMode = simulationMode ?? status;
  const resolvedFiles = simulationMode === "completed" ? simulationFiles : files;

  const gridClassName = useMemo(() => {
    if (resolvedFiles.length <= 1) {
      return "mx-auto grid max-w-xl grid-cols-1";
    }
    return "grid grid-cols-1 gap-4 lg:grid-cols-2";
  }, [resolvedFiles.length]);

  useEffect(() => {
    return () => {
      window.clearInterval(progressTimerRef.current);
      window.clearInterval(messageTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (resolvedMode !== "processing") {
      window.clearInterval(progressTimerRef.current);
      window.clearInterval(messageTimerRef.current);
      return;
    }

    setProgress(0);
    setMessageIndex(0);

    progressTimerRef.current = window.setInterval(() => {
      setProgress((current) => {
        const next = current + 2;
        return next >= 100 ? 100 : next;
      });
    }, 100);

    messageTimerRef.current = window.setInterval(() => {
      setMessageIndex((current) => (current + 1) % STATUS_COPY.length);
    }, 1000);

    return () => {
      window.clearInterval(progressTimerRef.current);
      window.clearInterval(messageTimerRef.current);
    };
  }, [resolvedMode]);

  const startSimulation = (count) => {
    setSimulationFiles([]);
    setSimulationMode("processing");

    window.clearTimeout(window.__docPanelTimeout);
    window.__docPanelTimeout = window.setTimeout(() => {
      setSimulationFiles(createSimulatedFiles(count));
      setSimulationMode("completed");
      setProgress(100);
    }, 5000);
  };

  const handleReset = () => {
    setSimulationMode("waiting");
    setSimulationFiles([]);
    setProgress(0);
    setMessageIndex(0);
    if (onReset) onReset();
  };

  const handleDownload = (file) => {
    setDownloadingId(file.id);

    window.setTimeout(() => {
      if (file.downloadUrl) {
        const link = document.createElement("a");
        link.href = file.downloadUrl;
        link.download = file.name;
        link.target = "_blank";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      const toastId = `${file.id}-${Date.now()}`;
      setToasts((current) => [
        ...current,
        { id: toastId, message: `${file.name} — Downloaded successfully` },
      ]);
      setDownloadingId(null);

      window.setTimeout(() => {
        setToasts((current) => current.filter((toast) => toast.id !== toastId));
      }, 3500);
    }, 1400);
  };

  return (
    <div
      className="relative flex h-full flex-col font-sans"
      style={{
        "--panel-bg": "transparent",
        "--panel-surface": "var(--doc-panel-surface, #ffffff)",
        "--panel-muted": "var(--doc-panel-muted, #eef4fb)",
        "--panel-pill": "var(--doc-panel-pill, #ffffff)",
        "--panel-pill-text": "var(--doc-panel-pill-text, #557089)",
        "--panel-border": "var(--doc-panel-border, rgba(24, 95, 165, 0.14))",
        "--panel-foreground": "var(--doc-panel-foreground, #13283f)",
        "--panel-subtle": "var(--doc-panel-subtle, #68819b)",
        "--panel-mono": "var(--doc-panel-mono, #587391)",
        "--panel-overlay": "var(--doc-panel-overlay, rgba(248, 251, 255, 0.76))",
        fontFamily: '"DM Sans", sans-serif',
      }}
    >

      <div className="flex-1">
        <AnimatePresence mode="wait">
          {resolvedMode === "processing" ? (
            <ProcessingState progress={progress} messageIndex={messageIndex} />
          ) : resolvedMode === "completed" ? (
            <motion.div
              key="completed"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.28 }}
              className="px-5 py-5"
            >
              <div className={gridClassName}>
                {resolvedFiles.map((file) => (
                  <DocumentCard
                    key={file.id}
                    file={file}
                    downloading={downloadingId === file.id}
                    onDownload={handleDownload}
                  />
                ))}
              </div>
            </motion.div>
          ) : (
            <WaitingState />
          )}
        </AnimatePresence>
      </div>

      <ToastStack toasts={toasts} />
    </div>
  );
}
