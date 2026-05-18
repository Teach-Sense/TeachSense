import Session from "../models/Session.js";
import Lecturer from "../models/Lecturer.js";
import {
  transcribeAudio,
  generateSummary,
  generateQuestions,
  calculateComprehensionScore,
} from "../services/aiService.js";

export const uploadAudio = async (req, res) => {
  try {
    const session = await Session.findById(req.params.id);

    if (!session) {
      return res.status(404).json({ message: "Session not found" });
    }

    // Security: verify session belongs to the requesting lecturer
    if (session.lecturer.toString() !== req.lecturer._id.toString()) {
      return res.status(403).json({ message: "Not authorized to modify this session" });
    }

    if (!req.file) {
      return res.status(400).json({ message: "No audio file provided" });
    }

    session.audioUrl = req.file.path;

    console.log("Starting transcription...");
    const transcript = await transcribeAudio(req.file.path);
    console.log("Transcript done.");
    session.transcript = transcript;

    console.log("Generating summary...");
    const summary = await generateSummary(transcript);
    session.summary = summary;

    console.log("Generating questions...");
    const questions = await generateQuestions(transcript);
    session.questions = questions;

    console.log("Calculating comprehension score...");
    const comprehensionScore = await calculateComprehensionScore(transcript);
    session.comprehensionScore = comprehensionScore;

    await session.save();

    // Update lecturer's average teaching score
    const allSessions = await Session.find({
      lecturer: req.lecturer._id,
      comprehensionScore: { $exists: true, $gt: 0 },
    });

    if (allSessions.length > 0) {
      const avgScore =
        allSessions.reduce((sum, s) => sum + (s.comprehensionScore || 0), 0) /
        allSessions.length;

      await Lecturer.findByIdAndUpdate(req.lecturer._id, {
        teachingScore: Math.round(avgScore),
      });
    }

    res.json({
      message: "Audio processed successfully",
      transcript,
      summary,
      questions,
      comprehensionScore,
    });
  } catch (error) {
    console.error("UPLOAD ERROR:", error);
    res.status(500).json({ message: error.message });
  }
};