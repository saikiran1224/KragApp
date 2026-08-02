CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    document_id bigserial PRIMARY KEY,
    file_name   text NOT NULL,
    file_type   text NOT NULL,
    uploaded_at timestamp DEFAULT now() NOT NULL,
    metadata    jsonb
);

CREATE TABLE chunks (
    id           bigserial PRIMARY KEY,
    document_id  bigint REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_text   text NOT NULL,
    embedding    vector(512) NOT NULL,
    chunk_index  int NOT NULL,
    metadata     jsonb
);

CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops);
