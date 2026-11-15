"use client";

import Link from "next/link";
import {
  useRunEvents,
  StageInfo,
} from "@/lib/api";
import {
  CheckCircle2,
  Clock,
  Cpu,
  AlertTriangle,
  XCircle,
  Loader2,
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  HelpCircle,
  Flame,
  FileCheck,
} from "lucide-react";

interface PageProps {
  params: { id: string };
}

export default function RunTimelinePage({ params }: PageProps) {
  const runId = params.id;

  const {
    stages,
    llmCallCount,
    isDone,
    isFailed,
    error,
    runData,
  } = useRunEvents(runId);

  // Compute total duration across completed stages
  const totalElapsed = stages.reduce(
    (acc, s) => acc + (s.duration ? Number(s.duration) : 0),
    0
  );

  const getDecisionBadge = (decision?: string | null) => {
    switch (decision) {
      case "ADVANCE":
        return {
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
          label: "ADVANCE",
          color: "bg-emerald-50 text-emerald-800 border-emerald-300",
        };
      case "REVIEW":
        return {
          icon: <HelpCircle className="w-5 h-5 text-amber-600" />,
          label: "REVIEW",
          color: "bg-amber-50 text-amber-800 border-amber-300",
        };
      case "DO_NOT_ADVANCE":
        return {
          icon: <XCircle className="w-5 h-5 text-rose-600" />,
          label: "DO NOT ADVANCE",
          color: "bg-rose-50 text-rose-800 border-rose-300",
        };
      default:
        return {
          icon: <Clock className="w-5 h-5 text-slate-500" />,
          label: "PENDING",
          color: "bg-slate-100 text-slate-700 border-slate-300",
        };
    }
  };

  const decisionMeta = getDecisionBadge(runData?.decision);

  return (
    <div className="space-y-8">
      {/* Top Navigation & Status Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-5">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 border rounded-md hover:bg-slate-100 text-slate-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900">
                Evaluation Run: <span className="font-mono text-indigo-600">{runId}</span>
              </h1>
              {isDone && (
                <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Completed
                </span>
              )}
              {isFailed && (
                <span className="bg-rose-100 text-rose-800 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" />
                  Failed
                </span>
              )}
              {!isDone && !isFailed && (
                <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Processing
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live multi-agent telemetry stream via Server-Sent Events
            </p>
          </div>
        </div>

        {/* Telemetry Metric Cards */}
        <div className="flex items-center gap-3">
          <div className="bg-white border rounded-lg px-4 py-2 flex items-center gap-3 shadow-sm">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400">LLM Calls</p>
              <p className="text-lg font-bold text-slate-800 font-mono">
                {llmCallCount} <span className="text-xs font-normal text-slate-500">/ 7 max</span>
              </p>
            </div>
          </div>

          <div className="bg-white border rounded-lg px-4 py-2 flex items-center gap-3 shadow-sm">
            <Clock className="w-5 h-5 text-indigo-600" />
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400">Elapsed</p>
              <p className="text-lg font-bold text-slate-800 font-mono">
                {totalElapsed.toFixed(1)}s
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Error alert if run failed */}
      {error && (
        <div className="bg-rose-50 border-l-4 border-rose-500 p-4 rounded-r-md flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 mt-0.5 shrink-0" />
          <div className="text-sm text-rose-800">
            <p className="font-semibold">Pipeline Execution Failed</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Stage Timeline */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <h2 className="text-base font-semibold text-slate-900 mb-6 flex items-center justify-between">
          <span>Council Pipeline Timeline</span>
          <span className="text-xs font-normal text-slate-500">
            {stages.filter((s) => s.status === "completed").length} of {stages.length} stages completed
          </span>
        </h2>

        <div className="space-y-4 relative before:absolute before:left-5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
          {stages.map((stage) => {
            const isCompleted = stage.status === "completed";
            const isRunning = stage.status === "running";
            const isFailedStage = stage.status === "failed";

            return (
              <div
                key={stage.id}
                className="relative flex items-start gap-4 pl-1 group"
              >
                {/* Timeline Icon / Dot */}
                <div className="z-10 bg-white p-0.5 rounded-full ring-2 ring-white">
                  {isCompleted ? (
                    <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-sm">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                  ) : isRunning ? (
                    <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-sm">
                      <Loader2 className="w-5 h-5 animate-spin" />
                    </div>
                  ) : isFailedStage ? (
                    <div className="w-8 h-8 rounded-full bg-rose-600 text-white flex items-center justify-center shadow-sm">
                      <XCircle className="w-5 h-5" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-400 border border-slate-300 flex items-center justify-center">
                      <Clock className="w-4 h-4" />
                    </div>
                  )}
                </div>

                {/* Stage Details */}
                <div
                  className={`flex-1 border rounded-lg p-4 transition ${
                    isRunning
                      ? "border-indigo-300 bg-indigo-50/20 shadow-sm"
                      : isCompleted
                      ? "border-slate-200 bg-slate-50/50"
                      : "border-slate-100 bg-white opacity-70"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3
                        className={`text-sm font-semibold ${
                          isRunning ? "text-indigo-900" : "text-slate-900"
                        }`}
                      >
                        {stage.name}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {stage.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {stage.duration !== undefined && (
                        <span className="text-xs font-mono bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-700">
                          {stage.duration.toFixed(1)}s
                        </span>
                      )}
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium capitalize ${
                          isCompleted
                            ? "bg-emerald-100 text-emerald-800"
                            : isRunning
                            ? "bg-indigo-100 text-indigo-800"
                            : isFailedStage
                            ? "bg-rose-100 text-rose-800"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {stage.status}
                      </span>
                    </div>
                  </div>

                  {/* Optional Metadata details */}
                  {stage.meta && Object.keys(stage.meta).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-200/60 text-xs text-slate-600 flex flex-wrap gap-3">
                      {Object.entries(stage.meta)
                        .filter(([k]) => !["elapsed", "skipped"].includes(k))
                        .map(([k, v]) => (
                          <span key={k} className="bg-white/80 px-2 py-0.5 rounded border">
                            <strong className="font-semibold text-slate-700">{k}:</strong>{" "}
                            {typeof v === "object" ? JSON.stringify(v) : String(v)}
                          </span>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Result View Placeholder when run is done */}
      {isDone && (
        <div className="bg-white rounded-lg border-2 border-indigo-200 shadow-md p-6 space-y-6 animate-fade-in">
          {/* Header Banner */}
          <div className="bg-amber-50 border border-amber-300 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldAlert className="w-6 h-6 text-amber-700 shrink-0" />
              <div>
                <p className="text-sm font-bold text-amber-900">
                  Human Decision Required
                </p>
                <p className="text-xs text-amber-800">
                  Council recommendations are decision support only. An authorized recruiter must confirm all outcomes.
                </p>
              </div>
            </div>
            <span className="text-xs bg-amber-200 text-amber-900 px-2.5 py-1 rounded font-semibold">
              Policy Rule #8
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b pb-6">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Evaluation Completed
              </p>
              <h2 className="text-xl font-bold text-slate-900 mt-1">
                Council Verdict & Findings
              </h2>
            </div>

            {/* Decision Badge: text + icon + colour */}
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border font-bold text-base shadow-sm ${decisionMeta.color}`}
            >
              {decisionMeta.icon}
              <span>{decisionMeta.label}</span>
            </div>
          </div>

          {/* Result details preview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-slate-50 border rounded-lg p-4">
              <p className="text-xs text-slate-500 font-semibold uppercase">Council Score</p>
              <p className="text-2xl font-bold text-slate-900 font-mono mt-1">
                {runData?.council_score !== undefined && runData?.council_score !== null
                  ? runData.council_score
                  : "N/A"}
              </p>
            </div>

            <div className="bg-slate-50 border rounded-lg p-4">
              <p className="text-xs text-slate-500 font-semibold uppercase">Veto Badge</p>
              <div className="mt-1">
                {runData?.veto ? (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded">
                    <Flame className="w-3.5 h-3.5" /> Veto Triggered
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                    <ShieldCheck className="w-3.5 h-3.5" /> No Veto
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-50 border rounded-lg p-4">
              <p className="text-xs text-slate-500 font-semibold uppercase">AAR (Quorum / Unresolved)</p>
              <div className="mt-1 text-xs text-slate-700 space-y-1">
                <p>Quorum: <span className="font-semibold">{runData?.quorum ? "Met" : "Unmet"}</span></p>
                <p>Unresolved: <span className="font-semibold">{runData?.unresolved ? "Yes" : "No"}</span></p>
              </div>
            </div>
          </div>

          {/* Placeholder for full results view */}
          <div className="border border-dashed border-slate-300 rounded-lg p-8 text-center bg-slate-50/50 space-y-3">
            <FileCheck className="w-10 h-10 text-indigo-500 mx-auto" />
            <h3 className="text-base font-semibold text-slate-800">
              [Result View Placeholder]
            </h3>
            <p className="text-sm text-slate-600 max-w-xl mx-auto">
              Evaluation pipeline stages have completed successfully. Detailed verdict cards, agent scores, verified claim findings, debate transcripts, and executive chair summary will render here.
            </p>
            <div className="pt-2">
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-300 text-sm font-medium rounded-md text-slate-700 hover:bg-slate-50 shadow-sm"
              >
                Start Another Evaluation
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
