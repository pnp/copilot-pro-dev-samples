"""
Typed data contracts for the extraction pipeline stages.

Every stage receives and returns a dataclass. This enables:
  - Type checking at stage boundaries
  - Clear documentation of what each stage produces
  - Easy serialization for debugging/logging
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class StatementType(str, Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"


class QualityStatus(str, Enum):
    ACCEPTED = "accepted"       # >= 0.90
    REVIEW = "review"           # >= 0.70
    REJECTED = "rejected"       # < 0.70


# ---------------------------------------------------------------------------
# Pipeline options (input to the pipeline)
# ---------------------------------------------------------------------------

@dataclass
class PipelineOptions:
    """Options controlling pipeline behavior."""
    use_enrichment: bool = True
    requested_types: list[str] = field(
        default_factory=lambda: ["balance_sheet", "income_statement", "cash_flow"]
    )
    source_file_name: str = "document.pdf"
    backend: str = "cu"  # "cu" | "textract" | "pdfplumber"


# ---------------------------------------------------------------------------
# Stage 1: Analyze
# ---------------------------------------------------------------------------

@dataclass
class CandidateStatement:
    """A single statement candidate from the CU Locator."""
    statement_type: str
    title_raw: Optional[str] = None
    title_english: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    company_name: Optional[str] = None
    company_name_raw: Optional[str] = None
    report_language: Optional[str] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    is_consolidated: Optional[bool] = None
    accounting_standard: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for backward compatibility with existing code."""
        return {
            "statement_type": self.statement_type,
            "title_raw": self.title_raw,
            "title_english": self.title_english,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "company_name": self.company_name,
            "company_name_raw": self.company_name_raw,
            "report_language": self.report_language,
            "currency": self.currency,
            "unit": self.unit,
            "is_consolidated": self.is_consolidated,
            "accounting_standard": self.accounting_standard,
        }


@dataclass
class AnalyzeResult:
    """Output of Stage 1 (Analyze)."""
    candidates: list[CandidateStatement]
    markdown: str
    pages: list[dict]
    page_map: list[tuple[int, int, int]]
    enrichment_lookup: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stage 2: Select
# ---------------------------------------------------------------------------

@dataclass
class ScoredCandidate:
    """A candidate with its selection score."""
    candidate: CandidateStatement
    score: float
    rejection_reason: Optional[str] = None


@dataclass
class SelectResult:
    """Output of Stage 2 (Select)."""
    selected: dict[str, CandidateStatement]        # stype -> best candidate
    rejected: dict[str, list[ScoredCandidate]]      # stype -> rejected candidates
    scores: dict[str, list[ScoredCandidate]]         # stype -> all scored candidates


# ---------------------------------------------------------------------------
# Stage 3: Extract
# ---------------------------------------------------------------------------

@dataclass
class ExtractedStatement:
    """Parsed data for a single statement."""
    statement_type: str
    rows: list[str]               # row labels from parser
    columns: list[str]            # column headers from parser
    cells: list[dict]             # cell dicts from parser
    md_offset: int = 0
    md_end_offset: int = 0
    start_page: int = 0
    end_page: int = 0
    tables_merged: int = 1


@dataclass
class ExtractResult:
    """Output of Stage 3 (Extract)."""
    statements: dict[str, ExtractedStatement]       # stype -> extracted data
    failures: dict[str, str]                         # stype -> failure reason


# ---------------------------------------------------------------------------
# Stage 4: Enrich
# ---------------------------------------------------------------------------

@dataclass
class EnrichedStatement:
    """Statement with enrichment data applied."""
    statement_type: str
    v12_doc: dict                 # Complete v1.2 schema document
    company_name_verified: Optional[str] = None
    columns_translated: bool = False


@dataclass
class EnrichResult:
    """Output of Stage 4 (Enrich)."""
    statements: dict[str, EnrichedStatement]        # stype -> enriched doc


# ---------------------------------------------------------------------------
# Stage 5: Validate
# ---------------------------------------------------------------------------

@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    name: str
    passed: bool
    score: float           # 0.0 to 1.0
    weight: float          # check weight
    details: Optional[str] = None


@dataclass
class ValidatedStatement:
    """Statement with validation results."""
    statement_type: str
    v12_doc: dict
    quality_score: float
    status: QualityStatus
    checks: list[ValidationCheck]


@dataclass
class ValidateResult:
    """Output of Stage 5 (Validate)."""
    statements: dict[str, ValidatedStatement]


# ---------------------------------------------------------------------------
# Pipeline result (final output)
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Final output of the full pipeline."""
    output: dict                   # The result dict (summary + statements + confidence)
    validate_result: Optional[ValidateResult] = None
    analyze_result: Optional[AnalyzeResult] = None
    select_result: Optional[SelectResult] = None
