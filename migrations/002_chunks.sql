CREATE TABLE chunks (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id   BIGINT NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    chunk_index   INTEGER NOT NULL,
    content       TEXT NOT NULL,
    metadata      JSONB NOT NULL DEFAULT '{}',
    embedding     vector(384) NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Fast approximate nearest-neighbor search over embeddings (cosine distance)
CREATE INDEX chunks_embedding_idx ON chunks
    USING hnsw (embedding vector_cosine_ops);

-- Fast keyword search, used for hybrid retrieval in Step 5
CREATE INDEX chunks_search_vector_idx ON chunks USING gin (search_vector);

CREATE INDEX chunks_document_id_idx ON chunks (document_id);