CREATE TABLE visits (
  id INTEGER PRIMARY KEY,
  visited_at TEXT
);

CREATE TABLE mushrooms (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  culinaryvalue INTEGER,
  healthvalue INTEGER,
  color INTEGER,
  category INTEGER,
  FOREIGN KEY(culinaryvalue) REFERENCES culinaryvalues(id),
  FOREIGN KEY(healthvalue) REFERENCES healthvalues(id),
  FOREIGN KEY(color) REFERENCES colors(id),
  FOREIGN KEY(category) REFERENCES categories(id)
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  auth TEXT,
  lastlogon DATE,
  credits INTEGER DEFAULT 0
);

CREATE TABLE reports (
  id INTEGER PRIMARY KEY,
  uid INTEGER,
  date DATE,
  category INTEGER,
  color INTEGER,
  culinaryvalue INTEGER,
  blanched INTEGER DEFAULT 0,
  deleted INTEGER DEFAULT 0,
  FOREIGN KEY(uid) REFERENCES users(id),
  FOREIGN KEY(color) REFERENCES colors(id),
  FOREIGN KEY(category) REFERENCES categories(id)
  FOREIGN KEY(culinaryvalue) REFERENCES culinaryvalues(id)
);

CREATE TABLE symptomreport (
  id INTEGER PRIMARY KEY,
  uid INTEGER,
  date DATE,
  report_id INTEGER,
  healthvalue INTEGER,
  deleted INTEGER DEFAULT 0
  FOREIGN KEY(report_id) REFERENCES reports(id),
  FOREIGN KEY(healthvalue) REFERENCES healthvalues(id)
)

CREATE TABLE colors (
  id INTEGER PRIMARY KEY,
  hex TEXT,
  name TEXT
);

CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  name TEXT
);

CREATE TABLE culinaryvalues (
  id INTEGER PRIMARY KEY,
  name TEXT,
  description TEXT
);

CREATE TABLE healthvalues (
  id INTEGER PRIMARY KEY,
  name TEXT,
  description TEXT
);

CREATE TABLE tastes (
  id INTEGER PRIMARY KEY,
  name TEXT,
  description TEXT
);

CREATE TABLE report_tastes (
  report_id INTEGER,
  tastes_id INTEGER,
  FOREIGN KEY(report_id) REFERENCES reports(id),
  FOREIGN KEY(tastes_id) REFERENCES tastes(id)
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY,
  rid INTEGER,
  uid INTEGER,
  date DATE,
  message TEXT,
  deleted INTEGER DEFAULT 0,
  FOREIGN KEY(rid) REFERENCES reports(id),
  FOREIGN KEY(uid) REFERENCES users(id)
);