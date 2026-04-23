import { useState } from "react";
import ExamList from "./components/ExamList";
import TakeExam from "./components/TakeExam";
import Dashboard from "./components/Dashboard";
import CreateExam from "./components/CreateExam";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [selectedExam, setSelectedExam] = useState(null);

  const navigate = (p, exam = null) => {
    setSelectedExam(exam);
    setPage(p);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand">
            <span className="brand-icon">🎓</span>
            <div>
              <div className="brand-name">ProctorAI</div>
              <div className="brand-sub">by aumne.ai</div>
            </div>
          </div>
          <nav className="nav">
            {[
              { key: "dashboard", label: "📊 Dashboard" },
              { key: "exams", label: "📋 Exams" },
              { key: "create", label: "✏️ Create Exam" },
            ].map((item) => (
              <button
                key={item.key}
                className={`nav-btn ${page === item.key ? "active" : ""}`}
                onClick={() => navigate(item.key)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="main">
        {page === "dashboard" && <Dashboard />}
        {page === "exams" && <ExamList onTakeExam={(e) => navigate("take", e)} />}
        {page === "create" && <CreateExam onCreated={() => navigate("exams")} />}
        {page === "take" && selectedExam && (
          <TakeExam exam={selectedExam} onDone={() => navigate("dashboard")} />
        )}
      </main>
    </div>
  );
}
