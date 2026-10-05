"""인제스천 골격: 로더 -> 청커 -> 메타 부착 -> 임베딩 -> upsert.

벤더 중립. 임베딩/스토어 함수만 환경에 맞게 교체한다.
시크릿은 환경변수로만 (하드코딩 금지).
"""
from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass, field
from typing import Iterable


# ---------- 1. 청크 데이터 모델 (메타데이터 필수) ----------
@dataclass
class Chunk:
    text: str
    source: str          # 파일 경로 / URL
    title: str           # 문서 제목 (헤더 prepend 에 사용)
    chunk_index: int
    section: str = ""    # 섹션 경로 (예: "2.1 설치")
    url: str = ""        # 인용용 (있으면)
    doi: str = ""        # 논문이면
    extra: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        # upsert 안정 키: 같은 source+index 면 재인제스션 시 덮어쓰기
        raw = f"{self.source}::{self.chunk_index}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @property
    def embed_text(self) -> str:
        # 헤더 prepend: 임베딩 문맥 보강
        prefix = f"[{self.title}] {self.section}".strip()
        return f"{prefix}\n{self.text}" if prefix else self.text


# ---------- 2. 청킹 (재귀 분할 + 오버랩 기본) ----------
def chunk_text(
    text: str,
    title: str,
    source: str,
    *,
    target_tokens: int = 800,
    overlap_ratio: float = 0.15,
    section: str = "",
) -> list[Chunk]:
    """단순 토큰 근사(=단어*1.3) 기반 고정+오버랩.

    프로덕션: tiktoken/transformers tokenizer 로 교체, 표/코드 블록은
    분할 금지하도록 보호 로직 추가.
    """
    words = text.split()
    approx_words = max(1, int(target_tokens / 1.3))
    overlap = int(approx_words * overlap_ratio)
    step = max(1, approx_words - overlap)

    chunks: list[Chunk] = []
    for i, start in enumerate(range(0, len(words), step)):
        window = words[start : start + approx_words]
        if not window:
            break
        chunks.append(
            Chunk(
                text=" ".join(window),
                source=source,
                title=title,
                section=section,
                chunk_index=i,
            )
        )
    return chunks


# ---------- 3. 임베딩 (벤더 교체 지점) ----------
def embed(texts: list[str]) -> list[list[float]]:
    """동일 모델·동일 차원을 인제스천/쿼리 양쪽에서 사용할 것.

    예시는 Gemini text-embedding (2.x) / bge-m3 셀프호스트 중 택1.
    여기선 시그니처만 정의 — 실제 SDK 호출로 교체.
    """
    raise NotImplementedError("임베딩 SDK 호출로 교체하세요 (env 에서 키 로드)")


# ---------- 4. upsert (스토어 교체 지점) ----------
def upsert(chunks: list[Chunk], vectors: list[list[float]]) -> None:
    """pgvector / Qdrant / Pinecone 등. id 로 멱등 upsert.

    pgvector 예: INSERT ... ON CONFLICT (id) DO UPDATE.
    """
    raise NotImplementedError("벡터스토어 upsert 로 교체하세요")


# ---------- 파이프라인 ----------
def ingest_document(text: str, title: str, source: str) -> int:
    chunks = chunk_text(text, title=title, source=source)
    vectors = embed([c.embed_text for c in chunks])
    upsert(chunks, vectors)
    return len(chunks)


if __name__ == "__main__":
    assert os.environ.get("EMBED_API_KEY"), "EMBED_API_KEY 환경변수 필요"
    print("ingest 골격: embed()/upsert() 를 환경에 맞게 구현하세요")
