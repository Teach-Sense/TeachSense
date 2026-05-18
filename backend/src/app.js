import express from "express";
import cors from "cors";
import uploadRoutes from "./routes/uploadRoutes.js";
import authRoutes from "./routes/authRoutes.js";
import sessionRoutes from "./routes/sessionRoutes.js";

const app = express();

app.use(
  cors({
    origin: [ "http://localhost:5173",
             "http://localhost:5173",
            "http://localhost:5174",
          "http://localhost:5175",
           "http://localhost:5176",
          "http://localhost:5177",
          "http://localhost:5178",
          "http://localhost:5179",  
    ],
  
    credentials: true,
  })
);

app.use(express.json());
app.use("/uploads", express.static("uploads"));

app.get("/", (req, res) => {
  res.send("TeachSense API Running");
});

app.use("/api/auth", authRoutes);
app.use("/api/sessions", sessionRoutes);
app.use("/api/upload", uploadRoutes);

export default app;