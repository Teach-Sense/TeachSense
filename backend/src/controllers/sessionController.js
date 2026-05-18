import Session from "../models/Session.js";

export const createSession = async (req, res) => {
  try {
    const { title } = req.body;

    if (!title || !title.trim()) {
      return res.status(400).json({ message: "Session title is required" });
    }

    const session = await Session.create({
      lecturer: req.lecturer._id,
      title: title.trim(),
    });

    res.status(201).json(session);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export const getSessions = async (req, res) => {
  try {
    const sessions = await Session.find({ lecturer: req.lecturer._id }).sort({
      createdAt: -1,
    });
    res.json(sessions);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export const startSession = async (req, res) => {
  try {
    const session = await Session.findById(req.params.id);

    if (!session) {
      return res.status(404).json({ message: "Session not found" });
    }

    // Security: verify ownership
    if (session.lecturer.toString() !== req.lecturer._id.toString()) {
      return res.status(403).json({ message: "Not authorized" });
    }

    session.status = "active";
    await session.save();
    res.json(session);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export const endSession = async (req, res) => {
  try {
    const session = await Session.findById(req.params.id);

    if (!session) {
      return res.status(404).json({ message: "Session not found" });
    }

    // Security: verify ownership
    if (session.lecturer.toString() !== req.lecturer._id.toString()) {
      return res.status(403).json({ message: "Not authorized" });
    }

    session.status = "completed";
    await session.save();
    res.json(session);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

// Public route — no auth needed — for student view
export const getSessionForStudent = async (req, res) => {
  try {
    const session = await Session.findById(req.params.id).select(
      "title transcript summary questions comprehensionScore status createdAt"
    );

    if (!session) {
      return res.status(404).json({ message: "Session not found" });
    }

    if (session.status !== "completed") {
      return res.status(403).json({ message: "Session results are not yet available" });
    }

    res.json(session);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};