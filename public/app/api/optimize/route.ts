import { NextResponse } from "next/server";

const SYSTEM_PROMPT = `You are an expert language teaching assistant. A teacher has written a brief lesson context note to help generate a homework assignment for their student. Your job is to rewrite it into a clear, structured, and specific lesson context that will produce a better AI-generated assignment.

Improve it by:
- Specifying the grammar focus (tense, structure)
- Listing key vocabulary explicitly
- Noting the student's proficiency level (CEFR if inferable)
- Mentioning any topics, themes or activities covered
- Adding any useful detail that would help an AI tailor an avatar session

Keep it concise (3–5 sentences max). Return ONLY the improved context text — no preamble, no labels, no explanation.`;

export async function POST(request: Request) {
  const apiKey = process.env.MISTRAL_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "Missing MISTRAL_API_KEY environment variable" },
      { status: 500 },
    );
  }

  const body = (await request.json().catch(() => null)) as
    | { prompt?: string }
    | null;

  const prompt = body?.prompt?.trim();
  if (!prompt) {
    return NextResponse.json(
      { error: "prompt is required" },
      { status: 400 },
    );
  }

  const response = await fetch("https://api.mistral.ai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "mistral-large-latest",
      max_tokens: 500,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: `Teacher's original context:\n"${prompt}"` },
      ],
    }),
  });

  if (!response.ok) {
    const err = await response.text().catch(() => "Unknown error");
    return NextResponse.json(
      { error: `Mistral request failed: ${err}` },
      { status: response.status },
    );
  }

  const data = await response.json();
  const improved = data.choices?.[0]?.message?.content?.trim();

  return NextResponse.json({ improved: improved || null });
}