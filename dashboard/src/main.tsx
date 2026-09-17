import { createRoot } from "react-dom/client";
import { runtime } from "@runtime";
import { App } from "./App";
import "./styles.css";
import "./dataset.css";
import "./optimization.css";
import "./pilot.css";
import "./pilot-recovery.css";
createRoot(document.getElementById("root")!).render(<App runtime={runtime} />);
