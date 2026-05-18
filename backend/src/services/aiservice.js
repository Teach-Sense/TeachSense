import OpenAI from "openai";
import dotenv from "dotenv";
import fs from "fs";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const transcribeAudio = async (audioPath) => {
  try {
    const transcription = await openai.audio.transcriptions.create({
      file: fs.createReadStream(audioPath),
      model: "whisper-1",
    });
    return transcription.text;
  } catch (error) {
    console.error("OPENAI TRANSCRIPTION ERROR:", error);
    throw error;
  }
};

export const generateSummary = async (transcript) => {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini", // Fixed: was "gpt-4.1-mini"
      messages: [
        {
          role: "system",
          content:
            "You are an educational AI assistant that summarizes lectures clearly and concisely.",
        },
        {
          role: "user",
          content: `Summarize this lecture transcript in 3-5 paragraphs. 
Cover the key topics, important concepts, and main takeaways. 
Write clearly for students to review after class.

Transcript:
${transcript}`,
        },
      ],
    });
    return response.choices[0].message.content;
  } catch (error) {
    console.error("OPENAI SUMMARY ERROR:", error);
    throw error;
  }
};

export const generateQuestions = async (transcript) => {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini", // Fixed: was "gpt-4.1-mini"
      messages: [
        {
          role: "system",
          content:
            "You are an AI educational assistant that generates clear quiz questions from lectures.",
        },
        {
          role: "user",
          content: `Generate 5 educational quiz questions from this lecture transcript.
Format each question as:
Q1. [Question]
Answer: [Correct answer]

Make questions clear and test genuine understanding of the material.

Transcript:
${transcript}`,
        },
      ],
    });
    return response.choices[0].message.content;
  } catch (error) {
    console.error("OPENAI QUESTIONS ERROR:", error);
    throw error;
  }
};

export const calculateComprehensionScore = async (transcript) => {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are an educational AI. Respond ONLY with a JSON object and nothing else — no markdown, no backticks.",
        },
        {
          role: "user",
          content: `Based on the clarity, structure, and depth of this lecture transcript, estimate a student comprehension score from 0 to 100.

Return ONLY this JSON:
{"score": <number>}

Transcript:
${transcript}`,
        },
      ],
    });

    const raw = response.choices[0].message.content.trim();
    const parsed = JSON.parse(raw);
    return typeof parsed.score === "number" ? parsed.score : 75;
  } catch (error) {
    console.error("COMPREHENSION SCORE ERROR:", error);
    return 75; // fallback default
  }
};