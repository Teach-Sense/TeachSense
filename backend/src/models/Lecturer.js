import mongoose from "mongoose";

const lecturerSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    teachingScore: { type: Number, default: 0 },
  },
  { timestamps: true }
);

const Lecturer = mongoose.model("Lecturer", lecturerSchema);
export default Lecturer;