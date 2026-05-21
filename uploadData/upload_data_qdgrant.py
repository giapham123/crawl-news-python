import json
import uuid
import logging
import sys
import os
from pathlib import Path
from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod
import time
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from openai import OpenAI


# ==========================================
# 1. CONFIGURATION (SETTINGS)
# ==========================================
class Settings:
    # OpenAI
    # Lưu ý: Thay thế bằng API Key thực tế của bạn
    OPENAI_API_KEY = "***REMOVED_OPENAI_KEY***"
    OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"

    # Qdrant Connection
    QDRANT_HOST = "localhost"
    QDRANT_GRPC_PORT = 6334
    QDRANT_REST_PORT = 6333
    QDRANT_PREFER_GRPC = True
    API_KEY_QDRANT = ""

    # Collection Names (Default)
    QDRANT_COLLECTION_NAME_EC = "mafc_collection_ec"
    QDRANT_COLLECTION_NAME_SD = "mafc_collection_sd"

    # Ingestion Settings
    BATCH_SIZE = 100


settings = Settings()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ==========================================
# 2. EMBEDDING SERVICE
# ==========================================
class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required.")
        self.client = OpenAI(api_key=self.api_key)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # OpenAI limits input size, simple batching logic here if needed
        # but the Service handles main batching.
        tries = 0
        while True:
            try:
                # Replace newlines to avoid negative performance impact
                clean_texts = [t.replace("\n", " ") for t in texts]
                resp = self.client.embeddings.create(model=self.model, input=clean_texts)
                return [d.embedding for d in resp.data]
            except Exception as e:
                tries += 1
                if tries > 3:
                    logger.error(f"OpenAI embedding failed after retries: {e}")
                    raise
                time.sleep(1 * tries)


# ==========================================
# 3. QDRANT INGEST SERVICE
# ==========================================
class QdrantIngestService:
    """
    Service to ingest Q&A items into Qdrant via gRPC.
    Supports both SD (Structured Q1..Q10) and EC (Question List) formats.
    """

    def __init__(
            self,
            collection_name: str,
            data_json_path: str,
            embedding_provider: Optional[EmbeddingProvider] = None
    ):
        """
        Args:
            collection_name: Target Qdrant collection.
            data_json_path: Path to the JSON data file.
            embedding_provider: Instance of embedding provider.
        """
        self.collection_name = collection_name
        self.data_json_path = data_json_path
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()

        self.qdrant_host = settings.QDRANT_HOST
        self.grpc_port = int(settings.QDRANT_GRPC_PORT)
        self.batch_size = int(settings.BATCH_SIZE)

        logger.info(f"Connecting to Qdrant {self.qdrant_host}:{self.grpc_port} (Coll: {self.collection_name})")
        self.client = QdrantClient(
            host=self.qdrant_host,
            grpc_port=self.grpc_port,
            prefer_grpc=settings.QDRANT_PREFER_GRPC,
            api_key=settings.API_KEY_QDRANT,
            https=False  # Disable SSL/TLS for non-secure connections
        )

    def _resolve_data_path(self) -> Path:
        p = Path(self.data_json_path)
        if p.exists():
            return p.resolve()
        raise FileNotFoundError(f"Data file not found at: {p.absolute()}")

    def _load_data(self) -> List[Dict[str, Any]]:
        path = self._resolve_data_path()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Expected top-level JSON array of objects")
        return data

    def _ensure_collection(self, vector_size: int):
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' exists.")
        except Exception:
            logger.info(f"Collection '{self.collection_name}' not found. Creating with size {vector_size}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def _check_collection_has_data(self) -> bool:
        try:
            info = self.client.get_collection(self.collection_name)
            if info and info.points_count > 0:
                return True
            return False
        except Exception:
            return False

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self.embedding_provider.embed_batch(texts)

    def _generate_id_point(self, record: Dict[str, Any]) -> str:
        """Generate a deterministic ID for a record based on its content."""
        # Create a hash based on the record content for consistency
        content = json.dumps(record, sort_keys=True, ensure_ascii=False)
        hash_object = hashlib.sha256(content.encode('utf-8'))
        return hash_object.hexdigest()[:36]  # Use first 36 chars to mimic UUID format

    # ----------------------------------------------------------------
    # LOGIC FOR SD (Service Desk / Q1..Q10 format)
    # ----------------------------------------------------------------
    def ingest_sd(self):
        if self._check_collection_has_data():
            logger.warning(f"Collection '{self.collection_name}' already has data. Skipping ingestion.")
            return

        data = self._load_data()
        logger.info(f"Loaded {len(data)} SD records from {self.data_json_path}")

        all_texts = []
        all_metadata = []

        def _coerce_str_list(value: Any) -> List[str]:
            """Accept either str | list[str] | None and return cleaned list[str]."""
            if value is None:
                return []
            if isinstance(value, str):
                v = value.strip()
                return [v] if v else []
            if isinstance(value, list):
                out: List[str] = []
                for x in value:
                    if isinstance(x, str) and x.strip():
                        out.append(x.strip())
                return out
            return []

        # Extract logic for SD with proper metadata structure
        for i, record in enumerate(data):
            # Ensure id_point exists
            if "id_point" not in record or not record["id_point"]:
                record["id_point"] = self._generate_id_point(record)

            questions_list = _coerce_str_list(record.get("question"))
            situations_list = _coerce_str_list(record.get("situation"))
            answers_list = _coerce_str_list(record.get("answer"))

            # Metadata is root/original record context (keep both list + joined-string for compatibility)
            root_metadata = {
                "id_point": record.get("id_point", ""),
                "sheet_id": record.get("sheet_id", ""),
                "topic": record.get("topic"),
                "question": questions_list,
                "situation": "\n".join(situations_list),
                "situation_list": situations_list,
                "answer": "\n".join(answers_list),
                "answer_list": answers_list,
                "source_record": record,
            }

            # Extract Questions (ingest each question)
            for q_idx, q in enumerate(questions_list):
                point_uuid = str(uuid.uuid4())
                all_texts.append(q)
                all_metadata.append({
                    "id": point_uuid,
                    "payload": {
                        "text": q,
                        "field_name": "question",
                        "index": q_idx,
                        "metadata": root_metadata
                    },
                })

            # Extract Answer (ingest each answer)
            for a_idx, ans_text in enumerate(answers_list):
                point_uuid = str(uuid.uuid4())
                all_texts.append(ans_text)
                all_metadata.append({
                    "id": point_uuid,
                    "payload": {
                        "text": ans_text,
                        "field_name": "answer",
                        "index": a_idx,
                        "metadata": root_metadata
                    },
                })

            # Extract Situation (ingest each situation)
            for s_idx, sit_text in enumerate(situations_list):
                point_uuid = str(uuid.uuid4())
                all_texts.append(sit_text)
                all_metadata.append({
                    "id": point_uuid,
                    "payload": {
                        "text": sit_text,
                        "field_name": "situation",
                        "index": s_idx,
                        "metadata": root_metadata
                    },
                })

        self._process_and_upsert(all_texts, all_metadata)

    # ----------------------------------------------------------------
    # LOGIC FOR EC (E-Commerce / {"question": [], "answer": "", "id_point": ""} format)
    # ----------------------------------------------------------------
    def ingest_ec(self):
        if self._check_collection_has_data():
            logger.warning(f"Collection '{self.collection_name}' already has data. Skipping ingestion.")
            return

        data = self._load_data()
        logger.info(f"Loaded {len(data)} EC records from {self.data_json_path}")

        all_texts = []
        all_metadata = []

        for record in data:
            # Use existing id_point (UUID) or generate a new one
            if "id_point" not in record or not record["id_point"]:
                record["id_point"] = str(uuid.uuid4())
                print("Đã vào đây để tạo id")
            questions = record.get("question", [])
            answer = record.get("answer", "")

            # Shared metadata for all points of this record
            root_metadata = {
                "id_point": record["id_point"],
                "question": questions if isinstance(questions, list) else [],
                "answer": answer if isinstance(answer, str) else "",
            }

            # Embed Questions — each question becomes its own Qdrant point
            if isinstance(questions, list):
                for q_idx, q in enumerate(questions):
                    if q and isinstance(q, str) and q.strip():
                        all_texts.append(q.strip())
                        all_metadata.append({
                            "id": str(uuid.uuid4()),
                            "payload": {
                                "text": q.strip(),
                                "field_name": "question",
                                "index": q_idx,
                                "metadata": root_metadata,
                            },
                        })

            # Embed Answer — use id_point from record as stable Qdrant point ID
            if answer and isinstance(answer, str) and answer.strip():
                all_texts.append(answer.strip())
                all_metadata.append({
                    "id": record["id_point"],
                    "payload": {
                        "text": answer.strip(),
                        "field_name": "answer",
                        "metadata": root_metadata,
                    },
                })

        self._process_and_upsert(all_texts, all_metadata)

    # ----------------------------------------------------------------
    # SHARED UPSERT LOGIC
    # ----------------------------------------------------------------
    def _process_and_upsert(self, texts: List[str], metadata_list: List[Dict]):
        if not texts:
            logger.warning("No valid texts found to ingest.")
            return

        logger.info(f"Total points to create: {len(texts)}")

        # Process in batches
        total = len(texts)
        for i in range(0, total, self.batch_size):
            end_i = min(i + self.batch_size, total)
            batch_texts = texts[i:end_i]
            batch_meta = metadata_list[i:end_i]

            logger.info(f"Embedding batch {i} to {end_i}...")
            embeddings = self._embed_batch(batch_texts)

            if i == 0 and embeddings:
                self._ensure_collection(len(embeddings[0]))

            points = []
            for vec, meta in zip(embeddings, batch_meta):
                points.append(PointStruct(
                    id=meta["id"],
                    vector=vec,
                    payload=meta["payload"]
                ))

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points.")

        logger.info("Ingestion complete.")

    # ----------------------------------------------------------------
    # LOGIC FOR SD GROUPED (output.json: {sheet_id, topic, flows[], question[]})
    # ----------------------------------------------------------------
    def ingest_sd_grouped(self):
        """Ingest SD data từ format grouped (output.json):
        - Mỗi question  → 1 point,  metadata = full sheet item (điểm gốc)
        - Mỗi situation → 1 point,  metadata = full sheet item (điểm gốc)
        - Mỗi answer    → 1 point,  metadata = full sheet item (điểm gốc)
        """
        if self._check_collection_has_data():
            logger.warning(f"Collection '{self.collection_name}' already has data. Skipping ingestion.")
            return

        data = self._load_data()
        logger.info(f"Loaded {len(data)} grouped SD records from {self.data_json_path}")

        all_texts: List[str] = []
        all_metadata: List[Dict] = []

        for item in data:
            # Full original item = điểm gốc dùng làm metadata
            full_item = {
                "sheet_id": item.get("sheet_id", ""),
                "topic": item.get("topic", ""),
                "flows": item.get("flows", []),
                "question": item.get("question", []),
            }

            # --- Ingest từng question ---
            for q in item.get("question", []):
                if q and isinstance(q, str) and q.strip():
                    all_texts.append(q.strip())
                    all_metadata.append({
                        "id": str(uuid.uuid4()),
                        "payload": {
                            "text": q.strip(),
                            "field_name": "question",
                            "metadata": full_item,
                        },
                    })

            # --- Ingest từng situation và answer trong flows ---
            for flow in item.get("flows", []):
                point_id = flow.get("point_id", "")
                situation = flow.get("situation", "")
                answer = flow.get("answer", "")

                # Ingest situation
                if situation and isinstance(situation, str) and situation.strip():
                    all_texts.append(situation.strip())
                    all_metadata.append({
                        "id": str(uuid.uuid4()),
                        "payload": {
                            "text": situation.strip(),
                            "field_name": "situation",
                            "point_id": point_id,
                            "metadata": full_item,
                        },
                    })

                # Ingest answer
                if answer and isinstance(answer, str) and answer.strip():
                    all_texts.append(answer.strip())
                    all_metadata.append({
                        "id": str(uuid.uuid4()),
                        "payload": {
                            "text": answer.strip(),
                            "field_name": "answer",
                            "point_id": point_id,
                            "metadata": full_item,
                        },
                    })

        logger.info(f"Prepared {len(all_texts)} points (questions + situations + answers)")
        self._process_and_upsert(all_texts, all_metadata)
