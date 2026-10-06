import requests


class WikidataClient:
    """Client for retrieving structured ground truth from Wikidata."""

    API_URL = "https://www.wikidata.org/w/api.php"

    HEADERS = {
        "User-Agent": "Capstone-AI-Verification-System/1.0"
    }

    def search_entity(self, search_term: str) -> dict | None:
        """Search Wikidata for an entity."""

        response = requests.get(
            self.API_URL,
            params={
                "action": "wbsearchentities",
                "search": search_term,
                "language": "en",
                "format": "json",
                "limit": 5,
            },
            headers=self.HEADERS,
            timeout=15,
        )

        response.raise_for_status()

        results = response.json().get("search", [])

        if not results:
            return None

        return results[0]

    def get_entity(self, entity_id: str) -> dict:
        """Retrieve complete Wikidata entity data."""

        response = requests.get(
            self.API_URL,
            params={
                "action": "wbgetentities",
                "ids": entity_id,
                "format": "json",
            },
            headers=self.HEADERS,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        entity = data.get("entities", {}).get(entity_id)

        if not entity:
            raise ValueError(
                f"Wikidata entity not found: {entity_id}"
            )

        return entity

    def get_label(self, entity_id: str) -> str:
        """Get the English label of a Wikidata entity."""

        entity = self.get_entity(entity_id)

        return (
            entity.get("labels", {})
            .get("en", {})
            .get("value", entity_id)
        )

    def get_capital(self, country: str) -> dict:
        """
        Retrieve the capital of a country.

        Wikidata property P36 = capital.
        """

        country_entity = self.search_entity(country)

        if not country_entity:
            raise ValueError(
                f"Could not find country in Wikidata: {country}"
            )

        country_id = country_entity["id"]

        entity = self.get_entity(country_id)

        claims = entity.get("claims", {})

        capital_claims = claims.get("P36", [])

        if not capital_claims:
            raise ValueError(
                f"No capital statement found for {country}"
            )

        capital_id = capital_claims[0]["mainsnak"]["datavalue"]["value"]["id"]

        capital_name = self.get_label(capital_id)

        return {
            "label": capital_name,
            "source": "Wikidata",
            "source_id": capital_id,
            "entity_id": country_id,
        }

    def get_ground_truth(self, question: str) -> dict:
        """
        Retrieve ground truth for a supported factual question.
        """

        question_lower = question.lower().strip()

        # Example:
        # "What is the capital of France?"
        if "capital of " in question_lower:

            country = question_lower.split("capital of ", 1)[1]
            country = country.rstrip(" ?.!")

            result = self.get_capital(country)

            return {
                "question": question,
                "label": result["label"],
                "source": result["source"],
                "source_id": result["source_id"],
                "entity_id": result["entity_id"],
            }

        raise ValueError(
            "Question type is not currently supported by Wikidata ground-truth retrieval."
        )
