"use client";

import { ChangeEvent, SyntheticEvent, useState } from "react";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

type ParseResponse = {
  filename: string;
  worksheet_text: string;
};

type GenerateResponse = {
  learner_name: string;
  topic: string;
  exercise: string;
};

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while calling the backend.";
}

async function parseErrorResponse(response: Response) {
  const body = (await response.json().catch(() => null)) as
    | { detail?: string }
    | null;

  return body?.detail ?? `Request failed with status ${response.status}`;
}

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [learnerName, setLearnerName] = useState("");
  const [topic, setTopic] = useState("");
  const [worksheetText, setWorksheetText] = useState("");
  const [exercise, setExercise] = useState("");
  const [parseStatus, setParseStatus] = useState("");
  const [generateStatus, setGenerateStatus] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setSelectedFile(nextFile);
    setParseStatus("");
    setGenerateStatus("");
  };

  const handleParse = async (
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) => {
    event.preventDefault();

    if (!selectedFile) {
      setParseStatus("Choose a PDF or image before parsing.");
      return;
    }

    setIsParsing(true);
    setParseStatus("Parsing worksheet...");
    setExercise("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch(`${getApiBaseUrl()}/api/worksheet/parse`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as ParseResponse;
      setWorksheetText(data.worksheet_text);
      setParseStatus(`Parsed ${data.filename}.`);
    } catch (error) {
      setParseStatus(getErrorMessage(error));
    } finally {
      setIsParsing(false);
    }
  };

  const handleGenerate = async (
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) => {
    event.preventDefault();

    if (!worksheetText.trim()) {
      setGenerateStatus("Parse a worksheet or paste worksheet text first.");
      return;
    }

    if (!topic.trim()) {
      setGenerateStatus("Enter a topic for the new exercise.");
      return;
    }

    setIsGenerating(true);
    setGenerateStatus("Generating exercise...");

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/exercises/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          learner_name: learnerName,
          topic,
          worksheet_text: worksheetText,
        }),
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as GenerateResponse;
      setExercise(data.exercise);
      setGenerateStatus(`Exercise generated for ${data.topic}.`);
    } catch (error) {
      setGenerateStatus(getErrorMessage(error));
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f8f2e8_0%,#efe6d7_42%,#d8d0bf_100%)] px-6 py-10 text-stone-900">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8">
        <section className="rounded-[2rem] border border-stone-900/10 bg-[#fffaf0]/90 p-8 shadow-[0_30px_120px_rgba(73,52,35,0.12)] backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-amber-700">
            Mirror
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-stone-950 sm:text-6xl">
            Parse a lesson worksheet and generate a follow-up exercise from the
            Python backend.
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-stone-700">
            The Next frontend sends uploads and generation requests to FastAPI,
            while the backend reuses the existing OCR and exercise workflow from
            <code className="ml-1 rounded bg-stone-900 px-2 py-1 text-sm text-stone-50">
              src/mirror
            </code>
            .
          </p>
        </section>

        <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
          <section className="rounded-[2rem] bg-stone-950 p-6 text-stone-50 shadow-[0_25px_80px_rgba(28,25,23,0.35)]">
            <h2 className="text-2xl font-semibold">1. Parse worksheet</h2>
            <p className="mt-2 text-sm leading-6 text-stone-300">
              Upload a PDF or image. The backend extracts text and returns it to
              the browser for review.
            </p>

            <form className="mt-6 flex flex-col gap-4" onSubmit={handleParse}>
              <label className="flex flex-col gap-2 text-sm font-medium text-stone-200">
                Worksheet file
                <input
                  className="rounded-2xl border border-stone-700 bg-stone-900 px-4 py-3 text-stone-100 file:mr-4 file:rounded-full file:border-0 file:bg-amber-300 file:px-4 file:py-2 file:font-medium file:text-stone-950"
                  type="file"
                  accept=".pdf,image/png,image/jpeg,image/webp"
                  onChange={handleFileChange}
                />
              </label>
              <button
                className="rounded-full bg-amber-300 px-5 py-3 font-semibold text-stone-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:bg-stone-600 disabled:text-stone-300"
                disabled={isParsing}
                type="submit"
              >
                {isParsing ? "Parsing..." : "Parse worksheet"}
              </button>
            </form>

            <p className="mt-4 min-h-6 text-sm text-amber-200">{parseStatus}</p>
          </section>

          <section className="rounded-[2rem] border border-stone-900/10 bg-white/85 p-6 shadow-[0_25px_80px_rgba(87,70,45,0.12)]">
            <h2 className="text-2xl font-semibold text-stone-950">
              2. Generate exercise
            </h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              Review the parsed text, set the target topic, and call the
              generation workflow.
            </p>

            <form className="mt-6 flex flex-col gap-4" onSubmit={handleGenerate}>
              <label className="flex flex-col gap-2 text-sm font-medium text-stone-700">
                Learner name
                <input
                  className="rounded-2xl border border-stone-300 bg-stone-50 px-4 py-3 outline-none transition focus:border-amber-500"
                  onChange={(event) => setLearnerName(event.target.value)}
                  placeholder="Ava"
                  value={learnerName}
                />
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium text-stone-700">
                New topic
                <input
                  className="rounded-2xl border border-stone-300 bg-stone-50 px-4 py-3 outline-none transition focus:border-amber-500"
                  onChange={(event) => setTopic(event.target.value)}
                  placeholder="Travel plans"
                  value={topic}
                />
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium text-stone-700">
                Worksheet text
                <textarea
                  className="min-h-56 rounded-[1.5rem] border border-stone-300 bg-stone-50 px-4 py-3 outline-none transition focus:border-amber-500"
                  onChange={(event) => setWorksheetText(event.target.value)}
                  placeholder="Parsed worksheet text will appear here."
                  value={worksheetText}
                />
              </label>

              <button
                className="rounded-full bg-stone-950 px-5 py-3 font-semibold text-stone-50 transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
                disabled={isGenerating}
                type="submit"
              >
                {isGenerating ? "Generating..." : "Generate exercise"}
              </button>
            </form>

            <p className="mt-4 min-h-6 text-sm text-stone-600">
              {generateStatus}
            </p>
          </section>
        </div>

        <section className="rounded-[2rem] border border-stone-900/10 bg-[#fffdf8] p-6 shadow-[0_25px_80px_rgba(87,70,45,0.08)]">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-stone-950">
                Generated output
              </h2>
              <p className="text-sm leading-6 text-stone-600">
                The exercise text returned by the backend appears here.
              </p>
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-stone-400">
              API base URL: {getApiBaseUrl()}
            </p>
          </div>

          <pre className="mt-6 overflow-x-auto rounded-[1.5rem] bg-stone-950 p-5 text-sm leading-7 whitespace-pre-wrap text-stone-100">
            {exercise || "No exercise generated yet."}
          </pre>
        </section>
      </div>
    </main>
  );
}
