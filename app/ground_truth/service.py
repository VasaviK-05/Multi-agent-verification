
from app.ground_truth.wikidata_client import WikidataClient
from app.ground_truth.storage import save_ground_truth


class GroundTruthService:
    """Fetch and store ground truth for a validation."""

    def __init__(self):
        self._wikidata = WikidataClient()

    def get_and_save(
        self,
        question: str,
        validation_id: str,
        question_id: int,
    ):
        # 1. Fetch ground truth from Wikidata
        result = self._wikidata.get_ground_truth(question)

        if not result:
            return None

        # 2. Extract the label returned by Wikidata
        label = result["label"]
        source = result.get("source", "Wikidata")

        # 3. Store it against both the validation and question IDs
        return save_ground_truth(
            validation_id=validation_id,
            question_id=question_id,
            label=label,
            source=source,
        )