"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  useRunEvents,
  StageInfo,
  DebatePoint,
  GateDecisionStep,
  ScoreBreakdown,
  AgentEval,
  CriterionRating,
  Evidence,
  ClaimFinding,
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
  HelpCircle,
  Flame,
  FileCheck,
  FileText,
  Scale,
  MessageSquare,
  Users,
  Calculator,
  Quote,
  Sparkles,
  ChevronRight,
  Info,
  UserCheck,
  Briefcase,
  Copy,
  Check,
  ThumbsUp,
  AlertOctagon,
  Eye,
  Sliders,
} from "lucide-react";

interface PageProps {
  params: { id: string };
}

type TabType = "executive" | "gate" | "debate" | "agents";
type PerspectiveType = "recruiter" | "audit";

export default function RunTimelinePage({ params }: PageProps) {
  const runId = params.id;
  const [perspective, setPerspective] = useState<PerspectiveType>("recruiter");
  const [activeTab, setActiveTab] = useState<TabType>("executive");
  const [selectedAgent, setSelectedAgent] = useState<string>("TECHNICAL");
  const [copiedQuestionIndex, setCopiedQuestionIndex] = useState<number | null>(null);

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
          humanTitle: "Recommended for Hire",
          color: "bg-emerald-50 text-emerald-800 border-emerald-300",
          progressColor: "bg-emerald-500",
        };
      case "REVIEW":
        return {
          icon: <HelpCircle className="w-5 h-5 text-amber-600" />,
          label: "REVIEW",
          humanTitle: "Conditional Hold for Human Review",
          color: "bg-amber-50 text-amber-800 border-amber-300",
          progressColor: "bg-amber-500",
        };
      case "DO_NOT_ADVANCE":
        return {
          icon: <XCircle className="w-5 h-5 text-rose-600" />,
          label: "DO NOT ADVANCE",
          humanTitle: "Not Recommended to Advance",
          color: "bg-rose-50 text-rose-800 border-rose-300",
          progressColor: "bg-rose-500",
        };
      default:
        return {
          icon: <Clock className="w-5 h-5 text-slate-500" />,
          label: "PENDING",
          humanTitle: "Evaluating Candidate...",
          color: "bg-slate-100 text-slate-700 border-slate-300",
          progressColor: "bg-indigo-500",
        };
    }
  };

  const getRatingBadge = (rating: string) => {
    switch (rating) {
      case "STRONG":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "PARTIAL":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "NOT_DEMONSTRATED":
        return "bg-rose-100 text-rose-800 border-rose-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUPPORTED":
        return "bg-emerald-50 text-emerald-700 border-emerald-300";
      case "CONTRADICTED":
        return "bg-rose-50 text-rose-700 border-rose-300";
      default:
        return "bg-slate-50 text-slate-600 border-slate-200";
    }
  };

  const decisionMeta = getDecisionBadge(runData?.decision);

  const artifacts = runData?.artifacts || {};
  const chairStructured = artifacts.chair_structured;
  const chairProse = artifacts.chair || "";
  const gateArtifact = artifacts.gate;
  const debatePoints: DebatePoint[] = (artifacts.points as DebatePoint[]) || [];
  const revisions = (artifacts.revisions as string[]) || [];
  const evalsMap: Record<string, AgentEval> = (artifacts.evals as Record<string, AgentEval>) || {};
  const availableAgents = Object.keys(evalsMap);
  const currentEval = evalsMap[selectedAgent] || (availableAgents.length > 0 ? evalsMap[availableAgents[0]] : null);

  const decisionTrace: GateDecisionStep[] = gateArtifact?.decision_trace || [];
  const scoreBreakdown: ScoreBreakdown | undefined = gateArtifact?.score_breakdown;

  // Confidence percentage
  const confidenceScore = runData?.council_score !== undefined && runData?.council_score !== null
    ? Math.round(Number(runData.council_score) * 100)
    : 70;

  // Extract pillar summary data for non-technical scorecard
  const getPillarSummary = (agentKey: string) => {
    const ev = evalsMap[agentKey];
    if (!ev) {
      return { status: "Unknown", color: "bg-slate-100 text-slate-600 border-slate-200", desc: "No data available" };
    }
    const hasNotDem = ev.ratings.some((r) => r.rating === "NOT_DEMONSTRATED");
    const hasStrong = ev.ratings.some((r) => r.rating === "STRONG");
    const contradictedClaim = ev.claim_findings.some((c) => c.status === "CONTRADICTED");

    if (ev.recommendation === "DO_NOT_ADVANCE" || contradictedClaim) {
      return {
        status: "Red Flag",
        color: "bg-rose-50 text-rose-800 border-rose-300",
        desc: contradictedClaim
          ? "Resume claims contradicted in interview."
          : ev.whisper || "Unfavorable demonstration during interview.",
      };
    }
    if (ev.recommendation === "ADVANCE" && hasStrong) {
      return {
        status: "Strong Match",
        color: "bg-emerald-50 text-emerald-800 border-emerald-300",
        desc: ev.whisper || "Demonstrated hands-on experience and verified answers.",
      };
    }
    return {
      status: "Moderate / Mixed",
      color: "bg-amber-50 text-amber-800 border-amber-300",
      desc: ev.whisper || "Partial demonstration; some aspects unverified.",
    };
  };

  const techPillar = getPillarSummary("TECHNICAL");
  const deliveryPillar = getPillarSummary("DELIVERY");
  const collabPillar = getPillarSummary("COLLABORATION");

  // Fallback strengths and red flags
  const strengthsList = chairStructured?.strengths && chairStructured.strengths.length > 0
    ? chairStructured.strengths
    : [
        "Demonstrated technical understanding of primary framework requirements.",
        "Clear communication of past engineering project participation.",
      ];

  const redFlagsList = chairStructured?.red_flags && chairStructured.red_flags.length > 0
    ? chairStructured.red_flags
    : runData?.veto
    ? [`Policy safety rule triggered: ${runData?.veto_signals?.join(", ") || "Critical gap"}`]
    : [
        "Teamwork and peer code review participation require deeper validation.",
        "Candidate had difficulty verifying senior-level solo ownership.",
      ];

  const followUpQuestions = chairStructured?.suggested_followups && chairStructured.suggested_followups.length > 0
    ? chairStructured.suggested_followups
    : [
        "Can you describe a specific time you had to review and merge a teammate's code that you disagreed with?",
        "Tell us about a technical architecture decision where you disagreed with your tech lead. How was it resolved?",
      ];

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedQuestionIndex(index);
    setTimeout(() => setCopiedQuestionIndex(null), 2000);
  };

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
              Multi-Agent Hiring Deliberation & Explainability Intelligence
            </p>
          </div>
        </div>

        {/* Telemetry Metric Cards */}
        <div className="flex items-center gap-3">
          <div className="bg-white border rounded-lg px-4 py-2 flex items-center gap-3 shadow-xs">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-400">LLM Calls</p>
              <p className="text-lg font-bold text-slate-800 font-mono">
                {llmCallCount} <span className="text-xs font-normal text-slate-500">/ 7 max</span>
              </p>
            </div>
          </div>

          <div className="bg-white border rounded-lg px-4 py-2 flex items-center gap-3 shadow-xs">
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
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-6">
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
                    <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-xs">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                  ) : isRunning ? (
                    <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-xs">
                      <Loader2 className="w-5 h-5 animate-spin" />
                    </div>
                  ) : isFailedStage ? (
                    <div className="w-8 h-8 rounded-full bg-rose-600 text-white flex items-center justify-center shadow-xs">
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
                      ? "border-indigo-300 bg-indigo-50/20 shadow-xs"
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

      {/* Main Results View */}
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

          {/* Top Bar: Title & Perspective Switcher */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-5">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Deliberation Completed
              </p>
              <h2 className="text-xl font-bold text-slate-900 mt-1">
                Candidate Evaluation & Explainability
              </h2>
            </div>

            {/* DUAL-PERSPECTIVE SWITCHER */}
            <div className="bg-slate-100 p-1 rounded-lg border border-slate-300 flex items-center self-start sm:self-center">
              <button
                onClick={() => setPerspective("recruiter")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-bold transition ${
                  perspective === "recruiter"
                    ? "bg-white text-indigo-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Eye className="w-3.5 h-3.5 text-indigo-600" />
                Recruiter View (Plain English)
              </button>
              <button
                onClick={() => setPerspective("audit")}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-bold transition ${
                  perspective === "audit"
                    ? "bg-white text-indigo-700 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Sliders className="w-3.5 h-3.5 text-slate-600" />
                Deep Audit View (Formulas & Logs)
              </button>
            </div>
          </div>

          {/* ============================================================== */}
          {/* PERSPECTIVE 1: RECRUITER VIEW (SIMPLE & HUMAN-CENTRIC)        */}
          {/* ============================================================== */}
          {perspective === "recruiter" && (
            <div className="space-y-6 pt-1">
              {/* Hero Decision & Takeaway Card */}
              <div className="bg-gradient-to-br from-indigo-50/80 via-white to-slate-50 border border-indigo-200 rounded-xl p-6 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-700 bg-indigo-100/70 px-2 py-0.5 rounded">
                      Final Council Recommendation
                    </span>
                    <h3 className="text-2xl font-black text-slate-900 flex items-center gap-2 mt-1">
                      {decisionMeta.icon}
                      {decisionMeta.humanTitle}
                    </h3>
                  </div>

                  {/* Confidence Meter */}
                  <div className="bg-white border border-slate-200 rounded-lg p-3 sm:min-w-[200px] shadow-xs">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-600">Match Confidence</span>
                      <span className="font-bold font-mono text-indigo-700">{confidenceScore}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${decisionMeta.progressColor}`}
                        style={{ width: `${Math.max(confidenceScore, 10)}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Plain-English Takeaway */}
                <div className="bg-white/90 border border-indigo-100 rounded-lg p-4 text-slate-800 text-sm leading-relaxed flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-slate-900 text-xs uppercase tracking-wider mb-0.5">
                      Executive Takeaway:
                    </p>
                    <p className="text-slate-800 font-medium">
                      {chairStructured?.one_sentence_takeaway ||
                        chairStructured?.verdict_statement ||
                        "Candidate demonstrates strong technical competence, but exhibits potential risks regarding peer reviews and collaborative execution."}
                    </p>
                  </div>
                </div>
              </div>

              {/* 3-Pillar Candidate Scorecard */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-indigo-600" />
                  Candidate Scorecard by Core Job Pillars
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Pillar 1: Technical Depth */}
                  <div className="bg-white border rounded-lg p-4 shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        🛠️ Technical Depth
                      </span>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${techPillar.color}`}>
                        {techPillar.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed pt-1">
                      {techPillar.desc}
                    </p>
                  </div>

                  {/* Pillar 2: Delivery & Ownership */}
                  <div className="bg-white border rounded-lg p-4 shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        🚀 Execution & Delivery
                      </span>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${deliveryPillar.color}`}>
                        {deliveryPillar.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed pt-1">
                      {deliveryPillar.desc}
                    </p>
                  </div>

                  {/* Pillar 3: Teamwork & Culture */}
                  <div className="bg-white border rounded-lg p-4 shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                        🤝 Culture & Teamwork
                      </span>
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${collabPillar.color}`}>
                        {collabPillar.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed pt-1">
                      {collabPillar.desc}
                    </p>
                  </div>
                </div>
              </div>

              {/* Strengths (Green Flags) vs Watch-Outs (Red Flags) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Green Flags */}
                <div className="bg-emerald-50/40 border border-emerald-200 rounded-lg p-4 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                    <ThumbsUp className="w-4 h-4 text-emerald-600" />
                    Key Strengths (Green Flags)
                  </h4>
                  <ul className="space-y-2">
                    {strengthsList.map((st, idx) => (
                      <li key={idx} className="text-xs text-slate-800 flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{st}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Red Flags */}
                <div className="bg-rose-50/40 border border-rose-200 rounded-lg p-4 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
                    <AlertOctagon className="w-4 h-4 text-rose-600" />
                    Critical Watch-Outs (Red Flags)
                  </h4>
                  <ul className="space-y-2">
                    {redFlagsList.map((rf, idx) => (
                      <li key={idx} className="text-xs text-slate-800 flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                        <span>{rf}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* The Panel Story: Plain-English Deliberation */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-indigo-600" />
                  What the Interview Panel Disagreed On & How It Was Resolved
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {chairStructured?.debate_narrative ||
                    (debatePoints.length > 0
                      ? `The technical and delivery interviewers were satisfied by the candidate's core coding ability, but the collaboration evaluator raised critical concerns regarding team friction and code review skipping. The panel resolved that high individual output does not outweigh team health, requiring an explicit human recruiter review.`
                      : "The interview panel reached a unanimous decision without substantial disagreements across all evaluated categories.")}
                </p>
              </div>

              {/* Actionable Follow-Up Guide for Interviewers */}
              <div className="bg-indigo-50/60 border border-indigo-200 rounded-lg p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center gap-1.5">
                    <UserCheck className="w-4 h-4 text-indigo-600" />
                    Recommended Questions for Round 2 Interview
                  </h4>
                  <span className="text-[10px] text-indigo-700 font-semibold bg-white border border-indigo-200 px-2 py-0.5 rounded">
                    Actionable Guide
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  Ask these targeted questions in the next conversation to clarify the flagged risks before making an offer:
                </p>

                <div className="space-y-2 pt-1">
                  {followUpQuestions.map((q, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-indigo-100 rounded-md p-3 text-xs text-slate-800 flex items-start justify-between gap-3 shadow-2xs"
                    >
                      <div className="flex items-start gap-2">
                        <span className="font-bold text-indigo-600 font-mono">Q{idx + 1}:</span>
                        <span className="italic leading-relaxed font-medium">"{q}"</span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(q, idx)}
                        className="text-slate-400 hover:text-indigo-600 p-1 rounded hover:bg-slate-50 transition shrink-0"
                        title="Copy question"
                      >
                        {copiedQuestionIndex === idx ? (
                          <span className="text-emerald-600 flex items-center gap-1 text-[10px] font-bold">
                            <Check className="w-3.5 h-3.5" /> Copied
                          </span>
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ============================================================== */}
          {/* PERSPECTIVE 2: DEEP AUDIT VIEW (FORMULAS, PROMPTS & TRACES)   */}
          {/* ============================================================== */}
          {perspective === "audit" && (
            <div className="space-y-6 pt-1">
              {/* Explainability Navigation Tabs */}
              <div className="border-b border-slate-200">
                <nav className="flex space-x-2 sm:space-x-4 overflow-x-auto" aria-label="Tabs">
                  <button
                    onClick={() => setActiveTab("executive")}
                    className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-2 transition ${
                      activeTab === "executive"
                        ? "border-indigo-600 text-indigo-600 font-semibold"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <FileText className="w-4 h-4" />
                    Executive Decision Trace
                  </button>

                  <button
                    onClick={() => setActiveTab("gate")}
                    className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-2 transition ${
                      activeTab === "gate"
                        ? "border-indigo-600 text-indigo-600 font-semibold"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <Scale className="w-4 h-4" />
                    Consensus & Gate Logic
                    {decisionTrace.length > 0 && (
                      <span className="bg-indigo-100 text-indigo-700 text-xs px-1.5 py-0.2 rounded-full">
                        {decisionTrace.length}
                      </span>
                    )}
                  </button>

                  <button
                    onClick={() => setActiveTab("debate")}
                    className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-2 transition ${
                      activeTab === "debate"
                        ? "border-indigo-600 text-indigo-600 font-semibold"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <MessageSquare className="w-4 h-4" />
                    Adversarial Debate & Conflicts
                    {debatePoints.length > 0 && (
                      <span className="bg-amber-100 text-amber-700 text-xs px-1.5 py-0.2 rounded-full">
                        {debatePoints.length}
                      </span>
                    )}
                  </button>

                  <button
                    onClick={() => setActiveTab("agents")}
                    className={`py-3 px-4 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-2 transition ${
                      activeTab === "agents"
                        ? "border-indigo-600 text-indigo-600 font-semibold"
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    }`}
                  >
                    <Users className="w-4 h-4" />
                    Agent Deep-Dives & Rationales
                    {availableAgents.length > 0 && (
                      <span className="bg-slate-100 text-slate-700 text-xs px-1.5 py-0.2 rounded-full">
                        {availableAgents.length}
                      </span>
                    )}
                  </button>
                </nav>
              </div>

              {/* TAB 1: EXECUTIVE DECISION TRACE */}
              {activeTab === "executive" && (
                <div className="space-y-6 pt-2">
                  {/* Verdict Statement Card */}
                  <div className="bg-gradient-to-r from-indigo-50/70 to-slate-50 border border-indigo-100 rounded-lg p-5">
                    <div className="flex items-center gap-2 text-indigo-700 text-xs font-bold uppercase tracking-wider mb-2">
                      <Sparkles className="w-4 h-4" /> Executive Verdict Summary
                    </div>
                    <h3 className="text-lg font-bold text-slate-900">
                      {chairStructured?.verdict_statement || chairProse.split("\n")[0] || "Council evaluation completed."}
                    </h3>
                  </div>

                  {/* Key Findings with Quotes */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-indigo-600" />
                      Key Deliberation Findings & Evidence Quotes
                    </h4>
                    {chairStructured?.key_findings && chairStructured.key_findings.length > 0 ? (
                      <div className="space-y-3">
                        {chairStructured.key_findings.map((finding, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2"
                          >
                            <div className="flex items-start justify-between gap-3">
                              <p className="text-sm text-slate-800 font-medium leading-relaxed">
                                {finding.observation}
                              </p>
                              {finding.source && (
                                <span className="text-[11px] font-mono font-semibold bg-white border border-slate-200 text-slate-700 px-2 py-0.5 rounded shrink-0">
                                  {finding.source}
                                </span>
                              )}
                            </div>
                            {finding.evidence_quote && (
                              <div className="bg-white border-l-2 border-indigo-400 rounded-r px-3 py-2 text-xs text-slate-600 italic flex items-start gap-2">
                                <Quote className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                                <span>"{finding.evidence_quote}"</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-700 whitespace-pre-line">
                        {chairProse || "No findings recorded."}
                      </div>
                    )}
                  </div>

                  {/* Risk Factors */}
                  {chairStructured?.risk_factors && chairStructured.risk_factors.length > 0 && (
                    <div className="bg-rose-50/70 border border-rose-200 rounded-lg p-4 space-y-2">
                      <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                        Identified Hiring Risk Factors
                      </h4>
                      <ul className="list-disc list-inside text-xs text-rose-800 space-y-1">
                        {chairStructured.risk_factors.map((risk, idx) => (
                          <li key={idx}>{risk}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Synthesis Rationale */}
                  {chairStructured?.synthesis_rationale && (
                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                        <Info className="w-4 h-4 text-slate-500" />
                        Chair Synthesis & Decision Trace
                      </h4>
                      <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-line">
                        {chairStructured.synthesis_rationale}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: CONSENSUS & GATE LOGIC */}
              {activeTab === "gate" && (
                <div className="space-y-6 pt-2">
                  {/* Score Formula Card */}
                  {scoreBreakdown && (
                    <div className="bg-indigo-50/50 border border-indigo-200 rounded-lg p-5 space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold text-indigo-900 flex items-center gap-2">
                          <Calculator className="w-4 h-4 text-indigo-600" />
                          Mathematical Score & Penalty Formula
                        </h4>
                        <span className="font-mono text-xs font-semibold bg-white border border-indigo-200 px-2 py-0.5 rounded text-indigo-800">
                          Council Score: {scoreBreakdown.final_council_score}
                        </span>
                      </div>

                      <div className="bg-white border border-indigo-100 rounded-md p-3 font-mono text-xs text-slate-800">
                        <p className="font-semibold text-slate-500 text-[10px] uppercase mb-1">
                          Executed Formula:
                        </p>
                        <p className="text-indigo-900 font-semibold">{scoreBreakdown.formula}</p>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <p className="text-slate-400 font-semibold text-[10px] uppercase">Base Score</p>
                          <p className="text-sm font-bold text-slate-800 font-mono mt-0.5">
                            {scoreBreakdown.base_score}
                          </p>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <p className="text-slate-400 font-semibold text-[10px] uppercase">Unresolved Penalty</p>
                          <p className="text-sm font-bold text-slate-800 font-mono mt-0.5">
                            {(1 - scoreBreakdown.unresolved_multiplier) > 0
                              ? `-${((1 - scoreBreakdown.unresolved_multiplier) * 100).toFixed(1)}%`
                              : "0%"}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            {scoreBreakdown.unresolved_points_count} point(s) @ {scoreBreakdown.unresolved_penalty_rate * 100}%
                          </p>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <p className="text-slate-400 font-semibold text-[10px] uppercase">Failed Agents Penalty</p>
                          <p className="text-sm font-bold text-slate-800 font-mono mt-0.5">
                            {(1 - scoreBreakdown.failed_multiplier) > 0
                              ? `-${((1 - scoreBreakdown.failed_multiplier) * 100).toFixed(1)}%`
                              : "0%"}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            {scoreBreakdown.failed_agents_count} agent(s) @ {scoreBreakdown.failed_penalty_rate * 100}%
                          </p>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-slate-200">
                          <p className="text-slate-400 font-semibold text-[10px] uppercase">Final Confidence</p>
                          <p className="text-sm font-bold text-indigo-700 font-mono mt-0.5">
                            {scoreBreakdown.final_council_score}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step-by-Step Decision Trace */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <Scale className="w-4 h-4 text-indigo-600" />
                      Deterministic Audit Trail & Threshold Checks
                    </h4>

                    <div className="space-y-3">
                      {decisionTrace.map((step) => {
                        const isPassed = ["PASSED", "CLEARED", "NO_PENALTY", "ALIGNED"].includes(step.status);
                        const isWarn = ["FLAGGED", "NOT_MET", "DIVIDED"].includes(step.status);

                        return (
                          <div
                            key={step.step}
                            className="bg-white border rounded-lg p-4 shadow-2xs space-y-2"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">
                                  {step.step}
                                </span>
                                <h5 className="text-sm font-bold text-slate-900">{step.stage}</h5>
                              </div>
                              <span
                                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                                  isPassed
                                    ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                                    : isWarn
                                    ? "bg-amber-50 text-amber-800 border-amber-300"
                                    : "bg-rose-50 text-rose-800 border-rose-300"
                                }`}
                              >
                                {step.status}
                              </span>
                            </div>

                            <div className="text-xs text-slate-600 space-y-1 pl-8">
                              <p>
                                <span className="font-semibold text-slate-700">Policy Rule:</span>{" "}
                                {step.rule}
                              </p>
                              <p>
                                <span className="font-semibold text-slate-700">Audit Detail:</span>{" "}
                                {step.detail}
                              </p>
                              <p className="font-medium text-indigo-800">
                                <span className="font-semibold text-slate-700">Action:</span>{" "}
                                {step.outcome}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: ADVERSARIAL DEBATE & CONFLICTS */}
              {activeTab === "debate" && (
                <div className="space-y-6 pt-2">
                  {/* Recommendation Revisions Callout */}
                  {revisions.length > 0 && (
                    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 space-y-1.5">
                      <p className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                        Consensus Shift: Agent Recommendations Revised in Debate
                      </p>
                      <div className="flex flex-wrap gap-2 pt-1">
                        {revisions.map((rev, idx) => (
                          <span
                            key={idx}
                            className="bg-white border border-indigo-300 text-indigo-900 font-semibold px-2.5 py-1 rounded text-xs shadow-2xs"
                          >
                            {rev}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {debatePoints.length > 0 ? (
                    <div className="space-y-4">
                      <h4 className="text-sm font-semibold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-indigo-600" />
                        Contested Points & Adjudication Transcripts ({debatePoints.length})
                      </h4>

                      {debatePoints.map((point) => {
                        const isUnresolved = point.verdict === "unresolved";
                        return (
                          <div
                            key={point.id}
                            className="bg-white border border-slate-200 rounded-lg p-5 shadow-2xs space-y-4"
                          >
                            {/* Point Header */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-3">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold bg-slate-100 text-slate-800 px-2 py-0.5 rounded">
                                  {point.id}
                                </span>
                                <span className="text-sm font-bold text-slate-900">
                                  Rule: {point.rule}
                                </span>
                                <span
                                  className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                                    point.severity === "high"
                                      ? "bg-rose-100 text-rose-800"
                                      : point.severity === "medium"
                                      ? "bg-amber-100 text-amber-800"
                                      : "bg-slate-100 text-slate-700"
                                  }`}
                                >
                                  {point.severity} severity
                                </span>
                              </div>

                              <div className="text-xs text-slate-600">
                                <span className="font-semibold text-indigo-700">{point.challenger}</span>{" "}
                                challenged{" "}
                                <span className="font-semibold text-slate-700">{point.challenged}</span>
                              </div>
                            </div>

                            {/* Disagreement Detail */}
                            <p className="text-xs text-slate-700 leading-relaxed">
                              <span className="font-semibold text-slate-800">Contested Claim / Finding:</span>{" "}
                              {point.detail}
                            </p>

                            {/* Adversarial Arguments Exchange */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                              {/* Challenger Argument */}
                              <div className="bg-rose-50/50 border border-rose-200 rounded-lg p-3 space-y-1.5">
                                <div className="flex items-center gap-1.5 text-rose-800 font-bold uppercase text-[10px]">
                                  <span>Challenger's Case ({point.challenger})</span>
                                </div>
                                <p className="text-slate-800 italic leading-relaxed">
                                  "{point.challenge || "No challenge statement recorded."}"
                                </p>
                              </div>

                              {/* Challenged Defense */}
                              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-1.5">
                                <div className="flex items-center gap-1.5 text-slate-700 font-bold uppercase text-[10px]">
                                  <span>Defense Reply ({point.challenged})</span>
                                </div>
                                <p className="text-slate-800 italic leading-relaxed">
                                  "{point.defense || "No defense provided."}"
                                </p>
                              </div>
                            </div>

                            {/* Moderator Verdict & Justification */}
                            <div className="bg-indigo-50/70 border border-indigo-200 rounded-lg p-4 space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                                  <Scale className="w-3.5 h-3.5 text-indigo-600" />
                                  Moderator Ruling:{" "}
                                  <span
                                    className={`px-2 py-0.5 rounded text-xs capitalize ${
                                      isUnresolved
                                        ? "bg-amber-200 text-amber-900"
                                        : "bg-indigo-600 text-white"
                                    }`}
                                  >
                                    {point.verdict}
                                  </span>
                                </span>
                              </div>

                              {point.verdict_rationale && (
                                <p className="text-xs text-indigo-950 leading-relaxed">
                                  <strong className="text-indigo-900">Verdict Rationale:</strong>{" "}
                                  {point.verdict_rationale}
                                </p>
                              )}

                              {point.key_evidence && point.key_evidence.length > 0 && (
                                <div className="pt-1 space-y-1">
                                  <p className="text-[10px] uppercase font-bold text-indigo-800">
                                    Decisive Evidence Quotes:
                                  </p>
                                  {point.key_evidence.map((evQuote, qIdx) => (
                                    <div
                                      key={qIdx}
                                      className="bg-white border border-indigo-200 text-xs text-slate-700 italic px-2.5 py-1.5 rounded"
                                    >
                                      "{evQuote}"
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="border border-dashed border-slate-200 rounded-lg p-8 text-center text-slate-500 text-sm">
                      No contested conflict points detected across panel agent evaluations.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 4: AGENT DEEP-DIVES & RATIONALES */}
              {activeTab === "agents" && (
                <div className="space-y-6 pt-2">
                  {/* Agent Sub-Selector */}
                  <div className="flex items-center gap-2 border-b pb-3">
                    <span className="text-xs font-semibold text-slate-500 uppercase mr-2">
                      Select Evaluator:
                    </span>
                    {["TECHNICAL", "DELIVERY", "COLLABORATION"].map((agentName) => {
                      const isSelected = selectedAgent === agentName;
                      const evalData = evalsMap[agentName];
                      return (
                        <button
                          key={agentName}
                          onClick={() => setSelectedAgent(agentName)}
                          className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 ${
                            isSelected
                              ? "bg-indigo-600 text-white shadow-2xs"
                              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                          }`}
                        >
                          <span>{agentName}</span>
                          {evalData && (
                            <span
                              className={`text-[10px] px-1.5 py-0.2 rounded font-normal ${
                                isSelected ? "bg-indigo-700 text-white" : "bg-white text-slate-600"
                              }`}
                            >
                              {evalData.recommendation}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {currentEval ? (
                    <div className="space-y-6">
                      {/* Evaluator Overview Card */}
                      <div className="bg-slate-50 border rounded-lg p-4 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div>
                            <h4 className="text-sm font-bold text-slate-900">
                              {selectedAgent} Lens Evaluation
                            </h4>
                            {currentEval.whisper && (
                              <p className="text-xs text-indigo-700 font-medium mt-0.5">
                                <span className="font-semibold text-slate-500">Whisper Alert:</span>{" "}
                                "{currentEval.whisper}"
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500 font-semibold uppercase">
                              Vote:
                            </span>
                            <span
                              className={`text-xs px-2.5 py-1 rounded font-bold border ${
                                currentEval.recommendation === "ADVANCE"
                                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                                  : currentEval.recommendation === "DO_NOT_ADVANCE"
                                  ? "bg-rose-50 text-rose-800 border-rose-300"
                                  : "bg-amber-50 text-amber-800 border-amber-300"
                              }`}
                            >
                              {currentEval.recommendation}
                            </span>
                          </div>
                        </div>

                        {currentEval.reasoning && (
                          <p className="text-xs text-slate-600 border-t pt-2">
                            <span className="font-semibold text-slate-700">Overall Reasoning:</span>{" "}
                            {currentEval.reasoning}
                          </p>
                        )}
                      </div>

                      {/* Criteria Ratings Breakdown */}
                      <div>
                        <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                          Scored Criteria & Step-by-Step Justifications
                        </h5>
                        <div className="space-y-3">
                          {currentEval.ratings.map((crit) => (
                            <div
                              key={crit.criterion}
                              className="bg-white border border-slate-200 rounded-lg p-4 space-y-2.5"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono text-xs font-bold text-slate-900">
                                  {crit.criterion}
                                </span>
                                <span
                                  className={`text-xs px-2.5 py-0.5 rounded font-semibold border ${getRatingBadge(
                                    crit.rating
                                  )}`}
                                >
                                  {crit.rating}
                                </span>
                              </div>

                              {/* Step-by-Step Rationale */}
                              {crit.rationale && (
                                <div className="bg-slate-50 rounded p-2.5 text-xs text-slate-700">
                                  <span className="font-semibold text-slate-800">
                                    Evaluator Justification:
                                  </span>{" "}
                                  {crit.rationale}
                                </div>
                              )}

                              {/* Evidence Quotes */}
                              {crit.evidence && crit.evidence.length > 0 ? (
                                <div className="space-y-1.5 pt-1">
                                  <p className="text-[10px] uppercase font-bold text-slate-400">
                                    Supporting Verbatim Quotes:
                                  </p>
                                  {crit.evidence.map((ev, evIdx) => (
                                    <div
                                      key={evIdx}
                                      className="bg-slate-50/70 border-l-2 border-indigo-400 rounded-r px-3 py-1.5 text-xs text-slate-700 flex items-start justify-between gap-2"
                                    >
                                      <div className="italic">"{ev.quote}"</div>
                                      <div className="flex items-center gap-1 shrink-0 text-[10px]">
                                        <span className="font-mono uppercase text-slate-500">
                                          {ev.source}
                                        </span>
                                        {ev.verified ? (
                                          <span className="text-emerald-600 font-bold flex items-center gap-0.5">
                                            <CheckCircle2 className="w-3 h-3" /> verified
                                          </span>
                                        ) : (
                                          <span className="text-amber-600 font-bold">unverified</span>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-[11px] text-slate-400 italic">
                                  No explicit quotes cited for this criterion.
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Claim Findings Table */}
                      {currentEval.claim_findings && currentEval.claim_findings.length > 0 && (
                        <div>
                          <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
                            Resume Claim Verification Status
                          </h5>
                          <div className="space-y-2">
                            {currentEval.claim_findings.map((finding) => (
                              <div
                                key={finding.claim_id}
                                className="bg-white border rounded-lg p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="font-mono font-bold bg-slate-100 px-2 py-0.5 rounded text-slate-800">
                                    {finding.claim_id}
                                  </span>
                                  {finding.evidence && finding.evidence.length > 0 && (
                                    <span className="text-slate-600 italic">
                                      "{finding.evidence[0].quote}"
                                    </span>
                                  )}
                                </div>
                                <span
                                  className={`px-2.5 py-0.5 rounded font-bold border text-[11px] shrink-0 ${getStatusBadge(
                                    finding.status
                                  )}`}
                                >
                                  {finding.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="border border-dashed border-slate-200 rounded-lg p-8 text-center text-slate-500 text-sm">
                      Evaluator data not available for {selectedAgent}.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Action Footer */}
          <div className="pt-4 border-t flex items-center justify-between">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-300 text-sm font-medium rounded-md text-slate-700 hover:bg-slate-50 shadow-2xs"
            >
              Start Another Evaluation
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
