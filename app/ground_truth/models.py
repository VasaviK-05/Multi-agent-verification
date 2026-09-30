from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class GroundTruthRecord:
    ground_truth_id: UUID
    validation_id: UUID
    question_id: int
    label: str
    source: str
    labeled_at: datetime