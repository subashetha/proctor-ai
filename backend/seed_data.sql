-- seed_data.sql — Initial test data for the Online Exam Proctoring System
-- Run: sqlite3 proctoring.db < seed_data.sql

INSERT INTO exams (title, duration) VALUES
  ('Python Fundamentals', 60),
  ('Data Structures & Algorithms', 90),
  ('Machine Learning Basics', 120),
  ('SQL and Databases', 45),
  ('System Design Principles', 75);

INSERT INTO submissions (exam_id, user_name, suspicious, flag_reasons, time_taken, answers) VALUES
  (1, 'alice',   0, NULL,                          3200, '{"q1": "def add(a,b): return a+b", "q2": "print(sorted([3,1,2]))"}'),
  (1, 'bob',     1, 'COPY_PASTE_DETECTED',          180, '{"q1": "def add(a,b): return a+b", "q2": "def add(a,b): return a+b"}'),
  (1, 'charlie', 1, 'SUSPICIOUSLY_FAST_SUBMISSION',  30, '{"q1": "pass", "q2": "pass"}'),
  (2, 'diana',   0, NULL,                          5000, '{"q1": "O(n log n)", "q2": "Binary search"}'),
  (2, 'eve',     1, 'LONG_INACTIVITY_OR_OVERTIME', 7000, '{"q1": "not sure", "q2": "maybe quicksort"}'),
  (3, 'frank',   1, 'BLANK_SUBMISSION',                0, '{"q1": "", "q2": ""}');
