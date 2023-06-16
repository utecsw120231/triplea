DROP TABLE IF EXISTS story CASCADE;
DROP TABLE IF EXISTS image CASCADE;
DROP TABLE IF EXISTS style CASCADE;

CREATE TABLE story (
  story_id SERIAL PRIMARY KEY,
  user_email TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE image (
  hash TEXT PRIMARY KEY,
  story_id INTEGER NOT NULL,
  FOREIGN KEY (story_id) REFERENCES story(story_id)
);

CREATE TABLE style (
  user_email TEXT NOT NULL,
  style TEXT NOT NULL,
  PRIMARY KEY (user_email, style)
);
