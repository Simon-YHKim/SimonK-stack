-- pgvector 벡터스토어 골격 (Postgres / Supabase)
-- 벡터 + BM25(전문검색) 하이브리드를 한 DB 에서. $0/mo 스택 기본값.
-- 차원(1024)은 선택한 임베딩 모델에 맞춰 수정. 인제스천/쿼리 동일해야 함.

create extension if not exists vector;

create table if not exists rag_chunks (
  id            text primary key,        -- ingest.py 의 sha1(source::index)
  source        text not null,           -- 파일/URL
  title         text not null,
  section       text default '',
  url           text default '',
  doi           text default '',
  chunk_index   int  not null,
  content       text not null,
  -- 권한/테넌트 필터용 (멀티테넌트면 RLS 와 함께 필수)
  tenant_id     text,
  embedding     vector(1024) not null,
  fts           tsvector generated always as (to_tsvector('simple', content)) stored,
  created_at    timestamptz default now()
);

-- 벡터 인덱스: 데이터 적으면 ivfflat, 많으면 hnsw 권장
create index if not exists rag_chunks_embedding_hnsw
  on rag_chunks using hnsw (embedding vector_cosine_ops);

-- BM25(전문검색) 인덱스
create index if not exists rag_chunks_fts
  on rag_chunks using gin (fts);

create index if not exists rag_chunks_tenant on rag_chunks (tenant_id);

-- 하이브리드 검색: 벡터 top-k 와 BM25 top-k 를 RRF 로 융합
-- query_embedding: 쿼리 임베딩, query_text: 원문 쿼리
create or replace function hybrid_search(
  query_embedding vector(1024),
  query_text      text,
  match_count     int  default 20,
  rrf_k           int  default 60,
  p_tenant_id     text default null
)
returns table (id text, source text, title text, content text, score float)
language sql stable
as $$
  with vec as (
    select c.id, row_number() over (order by c.embedding <=> query_embedding) as rnk
    from rag_chunks c
    where p_tenant_id is null or c.tenant_id = p_tenant_id
    order by c.embedding <=> query_embedding
    limit match_count
  ),
  kw as (
    select c.id, row_number() over (
      order by ts_rank_cd(c.fts, plainto_tsquery('simple', query_text)) desc
    ) as rnk
    from rag_chunks c
    where (p_tenant_id is null or c.tenant_id = p_tenant_id)
      and c.fts @@ plainto_tsquery('simple', query_text)
    limit match_count
  ),
  fused as (
    select coalesce(vec.id, kw.id) as id,
           coalesce(1.0 / (rrf_k + vec.rnk), 0) +
           coalesce(1.0 / (rrf_k + kw.rnk), 0) as score
    from vec full outer join kw on vec.id = kw.id
  )
  select c.id, c.source, c.title, c.content, f.score
  from fused f
  join rag_chunks c on c.id = f.id
  order by f.score desc
  limit match_count;
$$;

-- 멀티테넌트면 RLS 활성화 (권한별 문서 유출 방지 — authz-designer 연계)
-- alter table rag_chunks enable row level security;
