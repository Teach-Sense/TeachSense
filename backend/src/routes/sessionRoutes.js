import express from "express";
import protect from "../middleware/authMiddleware.js";
import {
  createSession,
  getSessions,
  startSession,
  endSession,
  getSessionForStudent,
} from "../controllers/sessionController.js";

const router = express.Router();

// Public route — student view (no auth)
router.get("/student/:id", getSessionForStudent);

// Protected routes
router.route("/").post(protect, createSession).get(protect, getSessions);
router.put("/:id/start", protect, startSession);
router.put("/:id/end", protect, endSession);

export default router;