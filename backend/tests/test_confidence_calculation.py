"""
Unit tests for confidence calculation components in retriever
"""
import pytest
from app.rag.retriever import RAGRetriever
from unittest.mock import MagicMock


class TestConfidenceCalculation:
    """Test confidence score calculation components"""

    @pytest.fixture
    def retriever(self):
        """Create a RAGRetriever instance for testing"""
        # Mock the dependencies
        retriever = RAGRetriever()
        return retriever

    def test_similarity_component(self, retriever):
        """Test similarity component calculation"""
        assert retriever._calculate_similarity_component(0.8) == 0.8
        assert retriever._calculate_similarity_component(0.0) == 0.0
        assert retriever._calculate_similarity_component(1.0) == 1.0

    def test_citation_component_no_docs(self, retriever):
        """Test citation component with no retrieved docs"""
        score = retriever._calculate_citation_component([], [])
        assert score == 0.3  # Neutral score when no docs

    def test_citation_component_no_citations(self, retriever):
        """Test citation component with docs but no citations"""
        docs = [{"id": "1"}, {"id": "2"}]
        citations = []
        score = retriever._calculate_citation_component(docs, citations)
        assert score == 0.2  # Base score when no citations

    def test_citation_component_all_cited(self, retriever):
        """Test citation component when all docs are cited"""
        docs = [{"id": "1"}, {"id": "2"}]
        citations = [{"source_id": "1"}, {"source_id": "2"}]
        score = retriever._calculate_citation_component(docs, citations)
        # Base 0.6 + ratio 0.3 * 1.0 + diversity 0.1 = 1.0
        assert abs(score - 1.0) < 0.01

    def test_citation_component_partial_citations(self, retriever):
        """Test citation component with partial citations"""
        docs = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        citations = [{"source_id": "1"}]  # 1 out of 3 cited
        score = retriever._calculate_citation_component(docs, citations)
        # Should be between 0.2 and 1.0
        assert 0.2 < score < 1.0
        assert score < 0.8  # Not great citation ratio

    def test_grounding_component_no_uncertainty(self, retriever):
        """Test grounding component with no uncertainty phrases"""
        response = "The answer is clearly stated in the documentation."
        score, penalty = retriever._calculate_grounding_component(response)
        assert score == 1.0
        assert penalty == 0

    def test_grounding_component_one_uncertainty(self, retriever):
        """Test grounding component with one uncertainty phrase"""
        response = "I don't have enough information to answer this question."
        score, penalty = retriever._calculate_grounding_component(response)
        assert score == 0.7  # 1.0 - (1 * 0.3)
        assert penalty == 1

    def test_grounding_component_multiple_uncertainties(self, retriever):
        """Test grounding component with multiple uncertainty phrases"""
        response = "I cannot find the information. The context doesn't contain relevant data."
        score, penalty = retriever._calculate_grounding_component(response)
        # 1.0 - (2 * 0.3) = 0.4, but capped at 0.3 minimum
        assert score >= 0.3
        assert penalty == 2

    def test_grounding_component_case_insensitive(self, retriever):
        """Test that grounding component is case-insensitive"""
        response1 = "I CANNOT FIND the information"
        response2 = "i cannot find the information"
        score1, penalty1 = retriever._calculate_grounding_component(response1)
        score2, penalty2 = retriever._calculate_grounding_component(response2)
        assert score1 == score2
        assert penalty1 == penalty2

    def test_query_quality_component_no_docs(self, retriever):
        """Test query quality component with no docs"""
        score = retriever._calculate_query_quality_component([])
        assert score == 1.0  # Default to high quality

    def test_query_quality_component_high_quality(self, retriever):
        """Test query quality component with high quality query"""
        docs = [{"query_quality": {"quality_score": 0.9, "issues": []}}]
        score = retriever._calculate_query_quality_component(docs)
        assert score == 0.9

    def test_query_quality_component_low_quality(self, retriever):
        """Test query quality component with low quality query"""
        docs = [{"query_quality": {"quality_score": 0.3, "issues": ["gibberish"]}}]
        score = retriever._calculate_query_quality_component(docs)
        assert score == 0.3

    def test_query_quality_component_missing_metadata(self, retriever):
        """Test query quality component with missing metadata"""
        docs = [{"id": "1"}]  # No query_quality field
        score = retriever._calculate_query_quality_component(docs)
        assert score == 1.0  # Default to high quality

    def test_combine_confidence_factors_default_weights(self, retriever):
        """Test combining confidence factors with default weights"""
        score = retriever._combine_confidence_factors(
            similarity_score=0.8,
            citation_score=0.6,
            grounding_score=1.0,
            query_quality_score=0.9
        )
        # 0.8*0.6 + 0.6*0.2 + 1.0*0.1 + 0.9*0.1 = 0.48 + 0.12 + 0.1 + 0.09 = 0.79
        assert abs(score - 0.79) < 0.01

    def test_combine_confidence_factors_custom_weights(self, retriever):
        """Test combining confidence factors with custom weights"""
        custom_weights = {
            'similarity': 0.5,
            'citation': 0.3,
            'grounding': 0.1,
            'query_quality': 0.1
        }
        score = retriever._combine_confidence_factors(
            similarity_score=0.8,
            citation_score=0.6,
            grounding_score=1.0,
            query_quality_score=0.9,
            weights=custom_weights
        )
        # 0.8*0.5 + 0.6*0.3 + 1.0*0.1 + 0.9*0.1 = 0.4 + 0.18 + 0.1 + 0.09 = 0.77
        assert abs(score - 0.77) < 0.01

    def test_combine_confidence_factors_bounds(self, retriever):
        """Test that combined score respects bounds"""
        # Test lower bound
        score_low = retriever._combine_confidence_factors(0.0, 0.0, 0.0, 0.0)
        assert score_low == 0.0

        # Test upper bound
        score_high = retriever._combine_confidence_factors(1.0, 1.0, 1.0, 1.0)
        assert score_high == 1.0

        # Test clamping (shouldn't happen in practice, but testing bounds)
        score = retriever._combine_confidence_factors(1.5, 1.5, 1.5, 1.5)
        assert score <= 1.0

    def test_calculate_confidence_score_integration(self, retriever):
        """Test full confidence score calculation"""
        docs = [
            {"id": "1", "query_quality": {"quality_score": 0.9}},
            {"id": "2", "query_quality": {"quality_score": 0.9}}
        ]
        citations = [{"source_id": "1"}, {"source_id": "2"}]
        response = "Here is the answer based on the sources provided."

        score = retriever._calculate_confidence_score(
            avg_similarity=0.85,
            retrieved_docs=docs,
            grounding_evidence=citations,
            response_text=response
        )

        # High similarity (0.85), all docs cited (1.0), no uncertainty (1.0), good quality (0.9)
        # 0.85*0.6 + 1.0*0.2 + 1.0*0.1 + 0.9*0.1 = 0.51 + 0.2 + 0.1 + 0.09 = 0.90
        assert 0.85 < score < 0.95
        assert score >= 0.0
        assert score <= 1.0

    def test_calculate_confidence_score_low_confidence(self, retriever):
        """Test confidence score with low confidence indicators"""
        docs = [{"id": "1", "query_quality": {"quality_score": 0.4}}]
        citations = []  # No citations
        response = "I don't have enough information to answer this question."

        score = retriever._calculate_confidence_score(
            avg_similarity=0.3,
            retrieved_docs=docs,
            grounding_evidence=citations,
            response_text=response
        )

        # Should be low confidence
        assert score < 0.5
        assert score >= 0.0

    def test_calculate_confidence_score_edge_cases(self, retriever):
        """Test confidence score with edge cases"""
        # No docs, no citations
        score1 = retriever._calculate_confidence_score(
            avg_similarity=0.0,
            retrieved_docs=[],
            grounding_evidence=[],
            response_text=""
        )
        assert 0.0 <= score1 <= 1.0

        # Perfect scores
        docs = [{"id": "1", "query_quality": {"quality_score": 1.0}}]
        citations = [{"source_id": "1"}]
        score2 = retriever._calculate_confidence_score(
            avg_similarity=1.0,
            retrieved_docs=docs,
            grounding_evidence=citations,
            response_text="Perfect answer"
        )
        assert score2 > 0.9
        assert score2 <= 1.0
