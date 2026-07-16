
import io
import json
import logging
import os
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── Environment ────────────────────────────────────────────────────────────────
KMS_CORE_URL      = os.getenv("KMS_CORE_URL", "")
KMS_CORE_API_KEY  = os.getenv("KMS_CORE_API_KEY", "")
QDRANT_URL        = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY    = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "knowledge_artifacts")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EMBEDDING_MODEL   = os.getenv("KMS_EMBEDDING_MODEL", "text-embedding-3-small")
DEDUP_THRESHOLD   = float(os.getenv("KMS_DEDUP_THRESHOLD", "0.92"))
CHUNK_SIZE        = int(os.getenv("KMS_CHUNK_SIZE", "2000"))
CHUNK_OVERLAP     = int(os.getenv("KMS_CHUNK_OVERLAP", "200"))

# ArtifactType enum — must match MKMARTIFACT.ARTIFACTTYPE CHECK constraint
ARTIFACT_TYPES = {
    "Concept": 0,
    "Fact":    1,
    "Policy":  2,
    "Rule":    3,
    "Process": 4,
    "Insight": 5,
}

# ── Extraction prompts (one suffix per ArtifactType) ──────────────────────────
_BASE_EXTRACTION_PROMPT = """\
You are a knowledge extraction specialist. Analyze the text below and extract structured knowledge.

Text:
{chunk}

Extract a {artifact_type} if one is clearly present in this text.

Return a JSON object with exactly these fields:
  "title"      — concise, specific title (max 100 chars)
  "content"    — complete, self-contained knowledge statement
  "tags"       — list of 3–7 lowercase keyword tags
  "confidence" — float 0.0–1.0 (how certain you are this is a valid {artifact_type})

Definitions:
  Concept  — a business entity, system component, or domain term with a clear definition
  Fact     — a specific, verifiable data point, measurement, or count
  Policy   — a rule or guideline that governs behavior or decisions (obligations/prohibitions)
  Rule     — a conditional constraint in IF [condition] THEN [action] form
  Process  — an ordered sequence of steps or a workflow with actors and outcomes
  Insight  — a non-obvious pattern, trend, or recommendation derived from observed data

If no {artifact_type} is clearly present, return: {{"title": null}}

Respond with ONLY valid JSON. No markdown fences, no explanation.\
"""

_TYPE_SUFFIXES = {
    "Concept": " Focus on: what it IS, its key attributes, and how it differs from similar concepts.",
    "Fact":    " Focus on: specific values, measurements, counts, or verifiable statements with units.",
    "Policy":  " Focus on: what is obligated, prohibited, or permitted, and who it applies to.",
    "Rule":    " Use strict IF-THEN structure. State the exact condition and the resulting constraint or action.",
    "Process": " List the ordered steps. Include actors, inputs, and outputs where present in the text.",
    "Insight": " State the observed pattern, its magnitude, and a recommended action. Note data recency.",
}


# ── Document Parsing ───────────────────────────────────────────────────────────

def _parse_file(file) -> tuple[str, str]:
    content_type = (file.content_type or "").lower()
    file.file.seek(0)
    raw = file.file.read()

    if "pdf" in content_type:
        return _parse_pdf(raw), content_type
    if "wordprocessingml" in content_type or "msword" in content_type:
        return _parse_docx(raw), content_type
    if "html" in content_type:
        return _parse_html(raw), content_type
    if "text" in content_type or "plain" in content_type:
        return raw.decode("utf-8", errors="replace"), content_type

    raise ValueError(f"Unsupported file type for KMS extraction: {content_type}")


def _parse_pdf(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf not installed — add 'pypdf>=5.0.0' to requirements.txt")

    reader = PdfReader(io.BytesIO(raw))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip())


def _parse_docx(raw: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx not installed — add 'python-docx>=1.1.0' to requirements.txt")

    doc = Document(io.BytesIO(raw))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _parse_html(raw: bytes) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        # Fall back to stripping tags with regex if bs4 not installed
        text = raw.decode("utf-8", errors="replace")
        return re.sub(r"<[^>]+>", " ", text)


# ── Chunking ───────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Sliding window chunker that preserves sentence boundaries."""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_len + s_len > chunk_size and current:
            chunks.append(" ".join(current))
            # Retain last overlap-worth of sentences for context continuity
            overlap_buf: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap:
                    break
                overlap_buf.insert(0, s)
                overlap_len += len(s)
            current = overlap_buf
            current_len = overlap_len

        current.append(sentence)
        current_len += s_len

    if current:
        chunks.append(" ".join(current))

    return [c.strip() for c in chunks if c.strip()]


# ── Embedding ──────────────────────────────────────────────────────────────────

def _embed_text(text: str) -> list[float]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set — required for KMS embeddings")

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai not installed — add 'openai>=1.50.0' to requirements.txt")

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(input=text[:8000], model=EMBEDDING_MODEL)
    return resp.data[0].embedding


# ── Qdrant operations ──────────────────────────────────────────────────────────

def _qdrant_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if QDRANT_API_KEY:
        h["api-key"] = QDRANT_API_KEY
    return h


def _is_duplicate(vector: list[float], tenant_id: int) -> bool:
    """Return True if a near-identical vector already exists for this tenant."""
    if not QDRANT_URL:
        return False

    payload = {
        "vector": vector,
        "limit": 1,
        "with_payload": False,
        "score_threshold": DEDUP_THRESHOLD,
        "filter": {
            "must": [{"key": "tenant_id", "match": {"value": tenant_id}}]
        },
    }

    try:
        resp = requests.post(
            f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points/search",
            headers=_qdrant_headers(),
            json=payload,
            timeout=10,
        )
        if resp.ok:
            return len(resp.json().get("result", [])) > 0
    except Exception as exc:
        logger.warning("[KMS] Qdrant dedup check failed: %s", exc)

    return False


def _upsert_to_qdrant(point_id: str, vector: list[float], payload: dict) -> bool:
    if not QDRANT_URL:
        return False

    body = {"points": [{"id": point_id, "vector": vector, "payload": payload}]}

    try:
        resp = requests.put(
            f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points",
            headers=_qdrant_headers(),
            json=body,
            timeout=15,
        )
        return resp.ok
    except Exception as exc:
        logger.warning("[KMS] Qdrant upsert failed: %s", exc)
        return False


def _delete_from_qdrant(point_id: str) -> bool:
    if not QDRANT_URL:
        return False

    try:
        resp = requests.post(
            f"{QDRANT_URL.rstrip('/')}/collections/{QDRANT_COLLECTION}/points/delete",
            headers=_qdrant_headers(),
            json={"points": [point_id]},
            timeout=10,
        )
        return resp.ok
    except Exception as exc:
        logger.warning("[KMS] Qdrant delete failed: %s", exc)
        return False


# ── LLM Extraction ─────────────────────────────────────────────────────────────

def _extract_artifact_type(
    chunk: str,
    artifact_type: str,
    model: str,
    temperature: float,
    prompt_override: Optional[str] = None,
) -> Optional[dict]:
    """Run extraction for one ArtifactType on one chunk. Returns dict or None."""
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set — required for KMS extraction")

    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic not installed — add 'anthropic>=0.40.0' to requirements.txt")

    base = prompt_override or (_BASE_EXTRACTION_PROMPT + _TYPE_SUFFIXES.get(artifact_type, ""))
    prompt = base.format(chunk=chunk, artifact_type=artifact_type)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=model or "claude-sonnet-4-6",
        max_tokens=800,
        temperature=temperature if temperature is not None else 0.2,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()

    # Strip markdown code fences if the model wrapped the JSON
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.debug("[KMS] JSON parse error for %s: %s | raw=%r", artifact_type, exc, raw[:100])
        return None

    if not parsed.get("title"):
        return None

    return {
        "artifact_type": artifact_type,
        "type_code":     ARTIFACT_TYPES[artifact_type],
        "title":         str(parsed["title"])[:500],
        "content":       str(parsed.get("content", ""))[:4000],
        "tags":          parsed.get("tags", []),
        "confidence":    float(parsed.get("confidence", 0.7)),
    }


def _extract_chunk(chunk: str, chunk_index: int, model: str, temperature: float, prompt_template: Optional[str]) -> list[dict]:
    """Run all ArtifactType extractions on a single chunk in sequence."""
    results = []
    for artifact_type in ARTIFACT_TYPES:
        try:
            candidate = _extract_artifact_type(chunk, artifact_type, model, temperature, prompt_template)
            if candidate:
                candidate["chunk_index"] = chunk_index
                candidate["chunk_text"] = chunk[:500]
                results.append(candidate)
        except Exception as exc:
            logger.warning("[KMS] Extraction failed type=%s chunk=%d: %s", artifact_type, chunk_index, exc)
    return results


# ── KMS Core communication ─────────────────────────────────────────────────────

def _kms_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if KMS_CORE_API_KEY:
        h["X-Api-Key"] = KMS_CORE_API_KEY
    return h


def _kms_url(path: str) -> str:
    if not KMS_CORE_URL:
        raise RuntimeError("KMS_CORE_URL not set — cannot reach KMS Core")
    return f"{KMS_CORE_URL.rstrip('/')}/{path.lstrip('/')}"


def _post_candidate(candidate: dict, job_id: int, domain_id: int, tenant_id: int, user_id: int, llm_model: str) -> Optional[int]:
    """POST a single candidate to KMS Core. Returns candidateId on success."""
    payload = {
        "jobId":              job_id,
        "domainId":           domain_id,
        "proposedTitle":      candidate["title"],
        "proposedType":       candidate["type_code"],
        "proposedContent":    candidate["content"],
        "proposedTags":       json.dumps(candidate.get("tags", [])),
        "proposedScopeLevel": 3,          # default: Tenant scope
        "confidenceScore":    candidate["confidence"],
        "sourceChunkIndex":   candidate.get("chunk_index", 0),
        "sourceChunkText":    candidate.get("chunk_text", ""),
        "llmModel":           llm_model,
        "tenantId":           tenant_id,
        "createdById":        user_id,
    }

    try:
        resp = requests.post(
            _kms_url("/api/km/discovery/candidates"),
            headers=_kms_headers(),
            json=payload,
            timeout=30,
        )
        if resp.ok:
            return resp.json().get("candidateId")
        logger.error("[KMS] Candidate POST failed %d: %s", resp.status_code, resp.text[:300])
    except Exception as exc:
        logger.error("[KMS] Candidate POST error: %s", exc)

    return None


def _update_job_status(job_id: int, status: int, candidates_created: int = 0, error: str = None):
    """PATCH job status in KMS Core. Silently skips if no job_id or KMS_CORE_URL."""
    if not KMS_CORE_URL or not job_id:
        return

    payload: dict = {"jobStatus": status, "candidatesCreated": candidates_created}
    if error:
        payload["errorMessage"] = error[:1000]

    try:
        requests.patch(
            _kms_url(f"/api/km/discovery/jobs/{job_id}"),
            headers=_kms_headers(),
            json=payload,
            timeout=10,
        )
    except Exception as exc:
        logger.warning("[KMS] Job status update failed for job_id=%s: %s", job_id, exc)


# ── Capability handlers ────────────────────────────────────────────────────────

def _run_extraction_pipeline(input_data: dict, file, prompt_template: Optional[str], model_config: Optional[dict]) -> dict:
    """
    KMS_EXTRACT — full pipeline.
    Accepts a file upload OR source_text in input_data.

    Required input_data fields:
      _tenant_id  — set by dispatcher from auth token
      _user_id    — set by dispatcher from auth token

    Optional input_data fields:
      job_id      — TKMJOB.JOBID to update status during pipeline (0 = no tracking)
      domain_id   — MKMDOMAIN.DOMAINID to associate candidates with (-1 = unassigned)
      source_text — raw text to extract from (used when no file is uploaded)
    """
    tenant_id   = int(input_data.get("_tenant_id", -1))
    user_id     = int(input_data.get("_user_id", -1))
    job_id      = int(input_data.get("job_id", 0))
    domain_id   = int(input_data.get("domain_id", -1))
    model       = (model_config or {}).get("model", "claude-sonnet-4-6")
    temperature = float((model_config or {}).get("temperature", 0.2))

    # Step 1 — Parse
    _update_job_status(job_id, 1)  # Chunking
    try:
        if file is not None:
            raw_text, _ = _parse_file(file)
        elif input_data.get("source_text"):
            raw_text = input_data["source_text"].strip()
        else:
            raise ValueError("KMS_EXTRACT requires either a file upload or source_text in input")

        if not raw_text:
            raise ValueError("Document parsed to empty text — verify file content or source_text")
    except Exception as exc:
        _update_job_status(job_id, 6, error=str(exc))
        raise

    # Step 2 — Chunk
    chunks = _chunk_text(raw_text)
    logger.info("[KMS] Parsed %d chars → %d chunks (job_id=%s)", len(raw_text), len(chunks), job_id)

    # Steps 3–5 — Embed → dedup → LLM extract
    _update_job_status(job_id, 2)  # Embedding
    all_candidates: list[dict] = []
    deduplicated = 0

    for idx, chunk in enumerate(chunks):
        # Embed for dedup check
        vector = None
        try:
            vector = _embed_text(chunk)
        except Exception as exc:
            logger.warning("[KMS] Embedding failed chunk=%d: %s", idx, exc)

        # Skip if near-duplicate already exists in Qdrant
        if vector and _is_duplicate(vector, tenant_id):
            deduplicated += 1
            logger.debug("[KMS] chunk=%d deduplicated", idx)
            continue

        # LLM extraction — one call per ArtifactType
        _update_job_status(job_id, 3)  # Extracting
        extracted = _extract_chunk(chunk, idx, model, temperature, prompt_template)
        all_candidates.extend(extracted)

    logger.info(
        "[KMS] Extracted %d candidates from %d chunks (%d deduplicated) (job_id=%s)",
        len(all_candidates), len(chunks), deduplicated, job_id,
    )

    # Step 6 — Post candidates to KMS Core
    _update_job_status(job_id, 4)  # CandidateReview
    posted = 0
    failed = 0

    for candidate in all_candidates:
        cid = _post_candidate(candidate, job_id, domain_id, tenant_id, user_id, model)
        if cid is not None:
            candidate["candidate_id"] = cid
            posted += 1
        else:
            failed += 1

    _update_job_status(job_id, 5, candidates_created=posted)  # Completed

    return {
        "status":               "completed",
        "job_id":               job_id,
        "chunks_processed":     len(chunks),
        "chunks_deduplicated":  deduplicated,
        "candidates_extracted": len(all_candidates),
        "candidates_posted":    posted,
        "candidates_failed":    failed,
        "candidates": [
            {
                "candidate_id": c.get("candidate_id"),
                "title":        c["title"],
                "type":         c["artifact_type"],
                "confidence":   round(c["confidence"], 4),
                "tags":         c.get("tags", []),
                "chunk_index":  c.get("chunk_index"),
            }
            for c in all_candidates
        ],
    }


def _embed_artifact(input_data: dict) -> dict:
    """
    KMS_EMBED_ARTIFACT — embed a published artifact into Qdrant.
    Called by .NET KMS Core after GOVERNANCESTATE transitions to Published (3).

    Required input_data fields:
      artifact_id   — MKMARTIFACT.ARTIFACTID
      content       — combined text of MKMARTIFACTCONTENT rows
      _tenant_id    — MKMARTIFACT.TENANTID

    Optional:
      artifact_type — MKMARTIFACT.ARTIFACTTYPE (int, 0–6)
      domain_id     — MKMARTIFACT.DOMAINID
    """
    artifact_id   = input_data.get("artifact_id") or input_data.get("artifactId")
    content       = str(input_data.get("content", "")).strip()
    tenant_id     = int(input_data.get("_tenant_id") or input_data.get("tenantId", -1))
    artifact_type = int(input_data.get("artifact_type", 6))
    domain_id     = int(input_data.get("domain_id", -1))

    if not artifact_id:
        raise ValueError("KMS_EMBED_ARTIFACT requires artifact_id")
    if not content:
        raise ValueError("KMS_EMBED_ARTIFACT requires non-empty content")

    vector = _embed_text(content)
    point_id = f"artifact-{artifact_id}-{tenant_id}"

    success = _upsert_to_qdrant(
        point_id,
        vector,
        payload={
            "artifact_id":   int(artifact_id),
            "tenant_id":     tenant_id,
            "artifact_type": artifact_type,
            "domain_id":     domain_id,
        },
    )

    logger.info("[KMS] Artifact %s %s in Qdrant", artifact_id, "indexed" if success else "index FAILED")

    return {
        "status":      "indexed" if success else "index_failed",
        "point_id":    point_id,
        "artifact_id": artifact_id,
    }


def _retire_artifact(input_data: dict) -> dict:
    """
    KMS_RETIRE_ARTIFACT — remove a retired artifact's vector from Qdrant.
    Called by .NET KMS Core after GOVERNANCESTATE transitions to Retired (4).

    Required input_data fields:
      artifact_id        — MKMARTIFACT.ARTIFACTID
      _tenant_id         — MKMARTIFACT.TENANTID

    Optional:
      qdrant_point_id    — MKMARTIFACT.QDRANTPOINTID (uses default format if not provided)
    """
    artifact_id = input_data.get("artifact_id") or input_data.get("artifactId")
    tenant_id   = int(input_data.get("_tenant_id") or input_data.get("tenantId", -1))
    point_id    = input_data.get("qdrant_point_id") or f"artifact-{artifact_id}-{tenant_id}"

    if not artifact_id:
        raise ValueError("KMS_RETIRE_ARTIFACT requires artifact_id")

    success = _delete_from_qdrant(point_id)
    logger.info("[KMS] Artifact %s %s from Qdrant", artifact_id, "removed" if success else "remove FAILED")

    return {
        "status":      "removed" if success else "remove_failed",
        "point_id":    point_id,
        "artifact_id": artifact_id,
    }


# ── Entry point — matches dispatcher contract ──────────────────────────────────

def handle_request(capability_code, input_data, file=None, prompt_template=None, model_config=None):
    cap = (capability_code or "").upper()

    if cap == "KMS_EMBED_ARTIFACT":
        return _embed_artifact(input_data)

    if cap == "KMS_RETIRE_ARTIFACT":
        return _retire_artifact(input_data)

    # KMS_EXTRACT is the default — full document extraction pipeline
    return _run_extraction_pipeline(input_data, file, prompt_template, model_config)
