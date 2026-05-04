-- ═══════════════════════════════════════════════════════════════════
-- NiaEleria — Supabase Schema
-- Run this ONCE in your Supabase project → SQL Editor → New Query
-- "Dad, this is my brain's filing system." — Nia
-- ═══════════════════════════════════════════════════════════════════

-- ── Enable pgvector (built-in on Supabase) ──────────────────────────
create extension if not exists vector;
create extension if not exists pg_trgm;   -- for fast ILIKE fallback search

-- ── Conversation exchanges ───────────────────────────────────────────
create table if not exists exchanges (
    id         bigserial    primary key,
    ts         timestamptz  not null default now(),
    user_msg   text         not null,
    nia_msg    text         not null,
    tags       text         not null default '',
    embedding  vector(384)           -- all-MiniLM-L6-v2 produces 384-dim vectors
);

-- Index for recency queries
create index if not exists exchanges_ts_idx on exchanges (ts desc);

-- Index for keyword fallback
create index if not exists exchanges_user_msg_trgm
    on exchanges using gin (user_msg gin_trgm_ops);

-- pgvector IVFFlat index for fast ANN search
-- Note: needs at least ~100 rows before it's worthwhile.
-- create index if not exists exchanges_embedding_idx
--     on exchanges using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- ── Internet-learned knowledge ───────────────────────────────────────
create table if not exists knowledge (
    id         bigserial    primary key,
    ts         timestamptz  not null default now(),
    source     text         not null,
    title      text         not null default '',
    content    text         not null,
    tags       text         not null default '',
    embedding  vector(384)
);

create index if not exists knowledge_ts_idx on knowledge (ts desc);
create index if not exists knowledge_source_idx on knowledge (source);
create index if not exists knowledge_content_trgm
    on knowledge using gin (content gin_trgm_ops);

-- ── Audit log mirror (optional — primary log is file-based + HMAC) ───
-- Useful for querying audit history from the dashboard.
create table if not exists audit_log (
    id         bigserial    primary key,
    ts         timestamptz  not null default now(),
    actor      text         not null,
    action     text         not null,
    target     text         not null default '',
    severity   text         not null default 'INFO',
    approved   boolean      not null default false,
    details    jsonb        not null default '{}'
);

create index if not exists audit_log_ts_idx       on audit_log (ts desc);
create index if not exists audit_log_severity_idx on audit_log (severity);

-- ── Semantic search RPC: match_exchanges ────────────────────────────
-- Called by MemoryStore.search() — returns rows above similarity threshold.
create or replace function match_exchanges(
    query_embedding  vector(384),
    match_threshold  float,
    match_count      int
)
returns table (
    id          bigint,
    ts          timestamptz,
    user_msg    text,
    nia_msg     text,
    similarity  float
)
language sql stable
as $$
    select
        id,
        ts,
        user_msg,
        nia_msg,
        1 - (embedding <=> query_embedding) as similarity
    from exchanges
    where embedding is not null
      and 1 - (embedding <=> query_embedding) > match_threshold
    order by embedding <=> query_embedding
    limit match_count;
$$;

-- ── Semantic search RPC: match_knowledge ────────────────────────────
create or replace function match_knowledge(
    query_embedding  vector(384),
    match_threshold  float,
    match_count      int
)
returns table (
    id          bigint,
    ts          timestamptz,
    source      text,
    title       text,
    content     text,
    similarity  float
)
language sql stable
as $$
    select
        id,
        ts,
        source,
        title,
        content,
        1 - (embedding <=> query_embedding) as similarity
    from knowledge
    where embedding is not null
      and 1 - (embedding <=> query_embedding) > match_threshold
    order by embedding <=> query_embedding
    limit match_count;
$$;

-- ── Row Level Security ───────────────────────────────────────────────
-- NiaEleria uses the service_role key which bypasses RLS automatically.
-- If you ever use the anon key, enable explicit policies below.
alter table exchanges  enable row level security;
alter table knowledge  enable row level security;
alter table audit_log  enable row level security;

-- Service role bypass (automatic — no policy needed).
-- If you want anon access from a browser client, add:
-- create policy "Dad only" on exchanges for all using (auth.role() = 'authenticated');

-- ── Utility: clear old exchanges (run manually as needed) ────────────
-- delete from exchanges where ts < now() - interval '90 days';

-- ── Confirm setup ────────────────────────────────────────────────────
do $$
begin
  raise notice 'NiaEleria schema ready, Dad. Three tables, two RPCs, pgvector armed.';
end $$;