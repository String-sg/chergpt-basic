
CREATE TABLE IF NOT EXISTS user_prompts (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    prompt_name TEXT NOT NULL,
    prompt_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    prompt_id INTEGER REFERENCES user_prompts(id),
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
