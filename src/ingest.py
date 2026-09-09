from pathlib import Path
import pandas as pd
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def read_file(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(p)).pages)
    if suffix == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".csv":
        return pd.read_csv(p).to_csv(index=False)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(p).to_csv(index=False)
    raise ValueError(f"Unsupported file type: {suffix}")

def chunk_document(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    ).split_text(text)

def ingest(path: str, department: str) -> list[dict]:
    return [{"text": c, "department": department, "source": Path(path).name}
            for c in chunk_document(read_file(path))]
