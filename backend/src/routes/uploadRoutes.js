import express from "express";
import protect from "../middleware/authMiddleware.js";
import upload from "../config/multer.js";
import { uploadAudio } from "../controllers/uploadController.js";

const router = express.Router();

router.post("/:id", protect, upload.single("audio"), uploadAudio);

export default router;