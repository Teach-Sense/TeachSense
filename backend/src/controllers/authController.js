import bcrypt from "bcryptjs";
import Lecturer from "../models/Lecturer.js";
import generateToken from "../utils/generateToken.js";

export const registerLecturer = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    const existingLecturer = await Lecturer.findOne({ email });
    if (existingLecturer) {
      return res.status(400).json({ message: "Lecturer already exists" });
    }

    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const lecturer = await Lecturer.create({ name, email, password: hashedPassword });

    res.status(201).json({
      _id: lecturer._id,
      name: lecturer.name,
      email: lecturer.email,
      teachingScore: lecturer.teachingScore,
      token: generateToken(lecturer._id),
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

export const loginLecturer = async (req, res) => {
  try {
    const { email, password } = req.body;
    const lecturer = await Lecturer.findOne({ email });

    if (lecturer && (await bcrypt.compare(password, lecturer.password))) {
      res.json({
        _id: lecturer._id,
        name: lecturer.name,
        email: lecturer.email,
        teachingScore: lecturer.teachingScore,
        token: generateToken(lecturer._id),
      });
    } else {
      res.status(401).json({ message: "Invalid email or password" });
    }
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};