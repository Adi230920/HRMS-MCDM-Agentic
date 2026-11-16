"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Sample,
  getSamples,
  createRun,
} from "@/lib/api";
import {
  FileText,
  Play,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  XCircle,
  Loader2,
  Sparkles,
  Cpu,
} from "lucide-react";

interface FormErrors {
  jd?: string;
  resume?: string;
  transcript?: string;
  candidateName?: string;
  general?: string;
}

export default function NewEvaluationPage() {
  const router = useRouter();

  const [samples, setSamples] = useState<Sample[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>("");
  const [loadingSamples, setLoadingSamples] = useState<boolean>(true);

  const [jd, setJd] = useState<string>("");
  const [resume, setResume] = useState<string>("");
  const [transcript, setTranscript] = useState<string>("");
  const [candidateName, setCandidateName] = useState<string>("");
  const [executionMode, setExecutionMode] = useState<"fast" | "live">("fast");

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [errors, setErrors] = useState<FormErrors>({});

  // Fetch samples on mount
  useEffect(() => {
    getSamples()
      .then((data) => {
        setSamples(data);
        setLoadingSamples(false);
      })
      .catch((err) => {
        console.error("Failed to load samples:", err);
        setLoadingSamples(false);
      });
  }, []);

  const totalChars = jd.length + resume.length + transcript.length;

  const validate = (): boolean => {
    const errs: FormErrors = {};

    if (!jd.trim()) {
      errs.jd = "Job description is required.";
    }

    if (!resume.trim()) {
      errs.resume = "Resume is required.";
    }

    if (!transcript.trim()) {
      errs.transcript = "Transcript is required.";
    } else {
      // Validate speaker labels
      const hasInterviewer = /(?:^|\n)\s*\[?INTERVIEWER\]?\s*:/i.test(transcript);
      const hasCandidate = /(?:^|\n)\s*\[?(?:CANDIDATE|INTERVIEWEE)\]?\s*:/i.test(
        transcript
      );

      if (!hasInterviewer || !hasCandidate) {
        errs.transcript =
          "Transcript requires both 'Interviewer:' and 'Candidate:' speaker labels.";
      }
    }

    if (totalChars > 30000) {
      errs.general = `Total character count (${totalChars.toLocaleString()} chars) exceeds 30,000 maximum limit.`;
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSampleChange = (sampleId: string) => {
    setSelectedSampleId(sampleId);
    if (!sampleId) return;

    const sample = samples.find((s) => s.id === sampleId);
    if (sample) {
      setJd(sample.jd || "");
      setResume(sample.resume || "");
      setTranscript(sample.transcript || "");
      setCandidateName(sample.candidate_name || "");
      setErrors({});
    }
  };

  const handleClear = () => {
    setJd("");
    setResume("");
    setTranscript("");
    setCandidateName("");
    setSelectedSampleId("");
    setErrors({});
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRunning) return;

    if (!validate()) {
      return;
    }

    setIsRunning(true);
    setErrors({});

    try {
      const isMock = executionMode === "fast";
      const response = await createRun(
        {
          jd: jd.trim(),
          resume: resume.trim(),
          transcript: transcript.trim(),
          candidate_name: candidateName.trim(),
          mock: isMock,
        },
        isMock
      );

      if (response && response.run_id) {
        router.push(`/runs/${response.run_id}`);
      } else {
        throw new Error("Missing run_id in response");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrors({ general: message });
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            New Evaluation
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Input candidate materials for automated multi-agent audit and evaluation.
          </p>
        </div>

        {/* Sample Loader */}
        <div className="flex items-center gap-3">
          <label
            htmlFor="sample-select"
            className="text-xs font-semibold uppercase tracking-wider text-slate-500"
          >
            Load Sample:
          </label>
          <select
            id="sample-select"
            value={selectedSampleId}
            onChange={(e) => handleSampleChange(e.target.value)}
            disabled={isRunning || loadingSamples}
            className="text-sm border border-slate-300 rounded-md px-3 py-1.5 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <option value="">-- Choose Sample Candidate --</option>
            {samples.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
          {loadingSamples && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
        </div>
      </div>

      {/* Execution Architecture Mode Toggle */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Execution Architecture Mode
          </span>
          <p className="text-xs text-slate-600 mt-0.5">
            Switch between instantaneous deterministic replay or live multi-provider LLM council deliberation.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg border border-slate-300">
          <button
            type="button"
            onClick={() => setExecutionMode("fast")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition ${
              executionMode === "fast"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            ⚡ Fast Verification Mode (Replay)
          </button>
          <button
            type="button"
            onClick={() => setExecutionMode("live")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition ${
              executionMode === "live"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-slate-600" />
            🌐 Live Multi-LLM Council
          </button>
        </div>
      </div>

      {/* General Inline Error Alert */}
      {errors.general && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
          <div className="text-sm text-red-800">
            <p className="font-semibold">Validation / Submission Error</p>
            <p>{errors.general}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleRun} className="space-y-6">
        {/* Candidate Name (Optional for redaction) */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="candidate-name"
              className="text-sm font-medium text-slate-800 flex items-center gap-2"
            >
              Candidate Name <span className="text-xs text-slate-500 font-normal">(Optional, used solely for PII redaction)</span>
            </label>
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              Never stored raw
            </span>
          </div>
          <input
            id="candidate-name"
            type="text"
            value={candidateName}
            onChange={(e) => setCandidateName(e.target.value)}
            placeholder="e.g. Priya Sharma or humble candidate"
            disabled={isRunning}
            className="w-full text-sm border border-slate-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
          />
        </div>

        {/* Job Description */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="jd"
              className="text-sm font-medium text-slate-800 flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-indigo-600" />
              Job Description <span className="text-red-500">*</span>
            </label>
            <span className="text-xs text-slate-500">{jd.length.toLocaleString()} chars</span>
          </div>
          <textarea
            id="jd"
            rows={4}
            value={jd}
            onChange={(e) => {
              setJd(e.target.value);
              if (errors.jd) setErrors((prev) => ({ ...prev, jd: undefined }));
            }}
            placeholder="Paste target job requirements and qualifications..."
            disabled={isRunning}
            className={`w-full text-sm font-mono border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 ${
              errors.jd ? "border-red-400 bg-red-50/20" : "border-slate-300"
            }`}
          />
          {errors.jd && <p className="text-xs text-red-600 font-medium">{errors.jd}</p>}
        </div>

        {/* Candidate Resume */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="resume"
              className="text-sm font-medium text-slate-800 flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-indigo-600" />
              Candidate Resume <span className="text-red-500">*</span>
            </label>
            <span className="text-xs text-slate-500">{resume.length.toLocaleString()} chars</span>
          </div>
          <textarea
            id="resume"
            rows={6}
            value={resume}
            onChange={(e) => {
              setResume(e.target.value);
              if (errors.resume) setErrors((prev) => ({ ...prev, resume: undefined }));
            }}
            placeholder="Paste candidate resume work history and claims..."
            disabled={isRunning}
            className={`w-full text-sm font-mono border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 ${
              errors.resume ? "border-red-400 bg-red-50/20" : "border-slate-300"
            }`}
          />
          {errors.resume && <p className="text-xs text-red-600 font-medium">{errors.resume}</p>}
        </div>

        {/* Interview Transcript */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <label
              htmlFor="transcript"
              className="text-sm font-medium text-slate-800 flex items-center gap-2"
            >
              <FileText className="w-4 h-4 text-indigo-600" />
              Interview Transcript <span className="text-red-500">*</span>
            </label>
            <span className="text-xs text-slate-500">
              {transcript.length.toLocaleString()} chars
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Must contain speaker labels: <code>Interviewer: ...</code> and <code>Candidate: ...</code>
          </p>
          <textarea
            id="transcript"
            rows={8}
            value={transcript}
            onChange={(e) => {
              setTranscript(e.target.value);
              if (errors.transcript) setErrors((prev) => ({ ...prev, transcript: undefined }));
            }}
            placeholder={`Interviewer: Walk me through your experience...\nCandidate: In my previous role...`}
            disabled={isRunning}
            className={`w-full text-sm font-mono border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 ${
              errors.transcript ? "border-red-400 bg-red-50/20" : "border-slate-300"
            }`}
          />
          {errors.transcript && (
            <p className="text-xs text-red-600 font-medium">{errors.transcript}</p>
          )}
        </div>

        {/* Footer Bar: Total chars, Clear button, Run Button */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t">
          <div className="text-xs text-slate-600">
            Total Input Size:{" "}
            <span
              className={`font-semibold ${
                totalChars > 30000 ? "text-red-600" : "text-slate-800"
              }`}
            >
              {totalChars.toLocaleString()} / 30,000 max
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleClear}
              disabled={isRunning}
              className="inline-flex items-center gap-1.5 px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-500 disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>

            <button
              type="submit"
              disabled={isRunning || totalChars > 30000}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-md shadow hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running Council...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Evaluation
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

