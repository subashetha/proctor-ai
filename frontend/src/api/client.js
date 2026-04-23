import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// Exams
export const createExam = (data) => api.post("/exams/", data);
export const listExams = () => api.get("/exams/");
export const getExam = (id) => api.get(`/exams/${id}`);

// Submissions
export const submitExam = (examId, data) => api.post(`/exams/${examId}/submit`, data);
export const listSubmissions = (flaggedOnly = false) =>
  api.get(`/submissions/?flagged_only=${flaggedOnly}`);
export const getSubmission = (id) => api.get(`/submissions/${id}`);

export default api;
