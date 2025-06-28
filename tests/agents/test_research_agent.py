"""
Comprehensive Test Suite for ResearchAgent

This module provides thorough testing for the ResearchAgent implementation,
covering all research capabilities including document analysis, competitive
intelligence, fact-checking, and literature review functionality.

Test Coverage:
- Research query execution and analysis
- Document analysis across multiple formats
- Competitive intelligence gathering
- Fact-checking and verification
- Citation generation and formatting
- Literature review and synthesis
- Trend analysis capabilities
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the ResearchAgent and related components
from agentical.agents.research_agent import (
    ResearchAgent, ResearchType, DocumentFormat, ResearchDepth,
    CredibilityLevel, CitationStyle, ResearchSource, ResearchQuery,
    ResearchResult, ResearchRequest, DocumentAnalysisRequest,
    CompetitiveAnalysisRequest
)
from agentical.db.models.agent import AgentType, AgentStatus
from agentical.core.exceptions import AgentExecutionError, ValidationError


@pytest.fixture
def research_agent():
    """Create ResearchAgent instance for testing."""
    return ResearchAgent(
        agent_id="test_research_agent",
        name="Test Research Agent",
        description="Research agent for testing"
    )


@pytest.fixture
def sample_research_request():
    """Create sample research request."""
    return {
        "query": "artificial intelligence trends 2024",
        "research_type": "academic",
        "depth": "standard",
        "max_sources": 10,
        "include_domains": ["arxiv.org", "nature.com"],
        "citation_style": "apa",
        "generate_report": True
    }


@pytest.fixture
def sample_document_request():
    """Create sample document analysis request."""
    return {
        "document_content": "This is a sample document for analysis. It contains key insights about technology trends and market developments. The document discusses various aspects of innovation and future implications.",
        "document_format": "txt",
        "analysis_type": ["summary", "key_points", "topics"],
        "extract_citations": True,
        "sentiment_analysis": True
    }


@pytest.fixture
def sample_competitive_request():
    """Create sample competitive analysis request."""
    return {
        "company_name": "TechCorp Inc",
        "competitors": ["CompetitorA", "CompetitorB"],
        "market_segment": "Cloud Computing",
        "analysis_areas": ["products", "pricing", "marketing"],
        "include_financial": True
    }


class TestResearchAgentBasics:
    """Test basic ResearchAgent functionality."""

    def test_agent_initialization(self, research_agent):
        """Test research agent initialization."""
        assert research_agent.agent_id == "test_research_agent"
        assert research_agent.name == "Test Research Agent"
        assert research_agent.agent_type == AgentType.RESEARCH
        assert research_agent.status == AgentStatus.ACTIVE

        # Check capabilities
        assert "academic" in research_agent.supported_research_types
        assert "competitive" in research_agent.supported_research_types
        assert "pdf" in research_agent.supported_formats
        assert "apa" in research_agent.citation_styles

    @pytest.mark.asyncio
    async def test_get_capabilities(self, research_agent):
        """Test capabilities reporting."""
        capabilities = await research_agent.get_capabilities()

        assert capabilities["agent_type"] == "research"
        assert "supported_research_types" in capabilities
        assert "supported_formats" in capabilities
        assert "capabilities" in capabilities
        assert "academic_research" in capabilities["capabilities"]
        assert "fact_checking" in capabilities["capabilities"]

    def test_research_type_enum(self):
        """Test ResearchType enum values."""
        assert ResearchType.ACADEMIC.value == "academic"
        assert ResearchType.MARKET.value == "market"
        assert ResearchType.COMPETITIVE.value == "competitive"
        assert ResearchType.TECHNICAL.value == "technical"

    def test_citation_style_enum(self):
        """Test CitationStyle enum values."""
        assert CitationStyle.APA.value == "apa"
        assert CitationStyle.MLA.value == "mla"
        assert CitationStyle.CHICAGO.value == "chicago"


class TestResearchExecution:
    """Test research execution functionality."""

    @pytest.mark.asyncio
    async def test_conduct_research_success(self, research_agent, sample_research_request):
        """Test successful research execution."""
        # Mock the internal search methods
        research_agent._search_sources = AsyncMock(return_value=[
            {
                "title": "AI Trends 2024",
                "url": "https://arxiv.org/paper1",
                "author": "Dr. Smith",
                "publication_date": datetime.utcnow(),
                "source_type": "academic"
            }
        ])

        research_agent._analyze_sources = AsyncMock(return_value=[
            ResearchSource(
                url="https://arxiv.org/paper1",
                title="AI Trends 2024",
                author="Dr. Smith",
                credibility=CredibilityLevel.HIGH,
                relevance_score=0.9,
                summary="Comprehensive analysis of AI trends",
                key_points=["AI adoption increasing", "Focus on ethics"]
            )
        ])

        result = await research_agent.execute_task(
            task_type="research_query",
            input_data=sample_research_request
        )

        assert result["status"] == "completed"
        assert result["query"] == sample_research_request["query"]
        assert result["sources_found"] >= 0
        assert "summary" in result
        assert "key_findings" in result
        assert "confidence_score" in result
        assert "report" in result

    @pytest.mark.asyncio
    async def test_conduct_research_academic_type(self, research_agent):
        """Test academic research execution."""
        request = {
            "query": "machine learning algorithms",
            "research_type": "academic",
            "depth": "deep",
            "max_sources": 5
        }

        # Mock academic database search
        research_agent._search_academic_databases = AsyncMock(return_value=[
            {
                "title": "Deep Learning Survey",
                "authors": ["Dr. A", "Dr. B"],
                "url": "https://arxiv.org/ml-survey",
                "publication_date": datetime.utcnow(),
                "source_type": "academic",
                "database": "arxiv"
            }
        ])

        research_agent._search_news_sources = AsyncMock(return_value=[])
        research_agent._search_web = AsyncMock(return_value=[])
        research_agent._analyze_sources = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="research_query",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["research_type"] == "academic"

    @pytest.mark.asyncio
    async def test_conduct_research_market_type(self, research_agent):
        """Test market research execution."""
        request = {
            "query": "smartphone market trends",
            "research_type": "market",
            "depth": "standard",
            "max_sources": 15
        }

        # Mock news source search
        research_agent._search_news_sources = AsyncMock(return_value=[
            {
                "title": "Smartphone Market Analysis",
                "author": "Market Analyst",
                "url": "https://reuters.com/market-analysis",
                "publication_date": datetime.utcnow(),
                "source_type": "news",
                "outlet": "Reuters"
            }
        ])

        research_agent._search_academic_databases = AsyncMock(return_value=[])
        research_agent._search_web = AsyncMock(return_value=[])
        research_agent._analyze_sources = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="research_query",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["research_type"] == "market"

    @pytest.mark.asyncio
    async def test_research_with_date_filtering(self, research_agent):
        """Test research with date range filtering."""
        request = {
            "query": "recent AI developments",
            "research_type": "news",
            "date_range_days": 30,
            "max_sources": 10
        }

        research_agent._search_sources = AsyncMock(return_value=[])
        research_agent._analyze_sources = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="research_query",
            input_data=request
        )

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_research_validation_error(self, research_agent):
        """Test research with validation errors."""
        invalid_request = {
            "query": "AB",  # Too short
            "research_type": "academic"
        }

        with pytest.raises(ValidationError):
            await research_agent.execute_task(
                task_type="research_query",
                input_data=invalid_request
            )


class TestDocumentAnalysis:
    """Test document analysis functionality."""

    @pytest.mark.asyncio
    async def test_document_analysis_success(self, research_agent, sample_document_request):
        """Test successful document analysis."""
        result = await research_agent.execute_task(
            task_type="document_analysis",
            input_data=sample_document_request
        )

        assert result["status"] == "completed"
        assert "document_metadata" in result
        assert "analysis_results" in result

        metadata = result["document_metadata"]
        assert metadata["format"] == "txt"
        assert metadata["word_count"] > 0
        assert metadata["character_count"] > 0

        analysis = result["analysis_results"]
        assert "summary" in analysis
        assert "key_points" in analysis
        assert "topics" in analysis
        assert "sentiment" in analysis

    @pytest.mark.asyncio
    async def test_document_analysis_with_url(self, research_agent):
        """Test document analysis with URL input."""
        request = {
            "document_url": "https://example.com/document.pdf",
            "document_format": "pdf",
            "analysis_type": ["summary"]
        }

        # Mock URL content extraction
        research_agent._extract_from_url = AsyncMock(
            return_value="Extracted PDF content for analysis"
        )

        result = await research_agent.execute_task(
            task_type="document_analysis",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["document_metadata"]["format"] == "pdf"

    @pytest.mark.asyncio
    async def test_document_analysis_multiple_formats(self, research_agent):
        """Test document analysis for different formats."""
        formats = ["pdf", "docx", "html", "markdown"]

        for doc_format in formats:
            request = {
                "document_content": f"Sample content in {doc_format} format",
                "document_format": doc_format,
                "analysis_type": ["summary"]
            }

            result = await research_agent.execute_task(
                task_type="document_analysis",
                input_data=request
            )

            assert result["status"] == "completed"
            assert result["document_metadata"]["format"] == doc_format

    @pytest.mark.asyncio
    async def test_document_analysis_validation_error(self, research_agent):
        """Test document analysis validation."""
        invalid_request = {
            "document_format": "pdf"
            # Missing both document_url and document_content
        }

        with pytest.raises(ValidationError):
            await research_agent.execute_task(
                task_type="document_analysis",
                input_data=invalid_request
            )


class TestCompetitiveAnalysis:
    """Test competitive analysis functionality."""

    @pytest.mark.asyncio
    async def test_competitive_analysis_success(self, research_agent, sample_competitive_request):
        """Test successful competitive analysis."""
        # Mock company research methods
        research_agent._research_company = AsyncMock(return_value={
            "company_name": "TechCorp Inc",
            "products": ["Product A", "Product B"],
            "strengths": ["Innovation", "Market presence"],
            "weaknesses": ["High costs", "Limited reach"]
        })

        research_agent._analyze_market_segment = AsyncMock(return_value={
            "segment": "Cloud Computing",
            "market_size": "$100B",
            "growth_rate": "20%"
        })

        result = await research_agent.execute_task(
            task_type="competitive_analysis",
            input_data=sample_competitive_request
        )

        assert result["status"] == "completed"
        assert result["company"] == "TechCorp Inc"
        assert result["market_segment"] == "Cloud Computing"
        assert "company_analysis" in result
        assert "competitor_analysis" in result
        assert "market_analysis" in result
        assert "swot_analysis" in result

    @pytest.mark.asyncio
    async def test_competitive_analysis_multiple_competitors(self, research_agent):
        """Test competitive analysis with multiple competitors."""
        request = {
            "company_name": "MainCorp",
            "competitors": ["Comp1", "Comp2", "Comp3"],
            "market_segment": "SaaS",
            "analysis_areas": ["products", "pricing"]
        }

        research_agent._research_company = AsyncMock(return_value={
            "company_name": "MainCorp",
            "products": ["SaaS Platform"]
        })

        research_agent._analyze_market_segment = AsyncMock(return_value={
            "segment": "SaaS"
        })

        result = await research_agent.execute_task(
            task_type="competitive_analysis",
            input_data=request
        )

        assert result["status"] == "completed"
        assert len(request["competitors"]) == 3
        assert "competitor_analysis" in result


class TestFactChecking:
    """Test fact-checking functionality."""

    @pytest.mark.asyncio
    async def test_fact_check_single_claim(self, research_agent):
        """Test fact-checking a single claim."""
        request = {
            "claims": ["The Earth is round"]
        }

        # Mock fact-check evidence search
        research_agent._search_fact_check_evidence = AsyncMock(return_value=[
            {
                "source": "scientific consensus",
                "verdict": "true",
                "evidence": "Overwhelming scientific evidence",
                "credibility": "high"
            }
        ])

        result = await research_agent.execute_task(
            task_type="fact_check",
            input_data=request
        )

        assert result["status"] == "completed"
        assert len(result["fact_check_results"]) == 1

        fact_result = result["fact_check_results"][0]
        assert fact_result["claim"] == "The Earth is round"
        assert "verdict" in fact_result
        assert "confidence" in fact_result
        assert "evidence" in fact_result

    @pytest.mark.asyncio
    async def test_fact_check_multiple_claims(self, research_agent):
        """Test fact-checking multiple claims."""
        request = {
            "claims": [
                "Water boils at 100°C",
                "The moon is made of cheese",
                "Python is a programming language"
            ]
        }

        research_agent._search_fact_check_evidence = AsyncMock(return_value=[
            {"source": "science", "credibility": "high"}
        ])

        result = await research_agent.execute_task(
            task_type="fact_check",
            input_data=request
        )

        assert result["status"] == "completed"
        assert len(result["fact_check_results"]) == 3

    @pytest.mark.asyncio
    async def test_fact_check_string_input(self, research_agent):
        """Test fact-checking with string input."""
        request = {
            "claims": "Single claim as string"
        }

        research_agent._search_fact_check_evidence = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="fact_check",
            input_data=request
        )

        assert result["status"] == "completed"
        assert len(result["fact_check_results"]) == 1


class TestCitationGeneration:
    """Test citation generation functionality."""

    @pytest.mark.asyncio
    async def test_citation_generation_apa(self, research_agent):
        """Test APA citation generation."""
        request = {
            "sources": [
                {
                    "title": "Research Paper Title",
                    "author": "Dr. Smith",
                    "url": "https://journal.com/paper",
                    "publication_date": "2024-01-01"
                }
            ],
            "style": "apa"
        }

        result = await research_agent.execute_task(
            task_type="citation_generation",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["style"] == "apa"
        assert len(result["citations"]) == 1
        assert "bibliography" in result

    @pytest.mark.asyncio
    async def test_citation_generation_mla(self, research_agent):
        """Test MLA citation generation."""
        request = {
            "sources": [
                {
                    "title": "Article Title",
                    "author": "Jane Doe",
                    "url": "https://example.com/article"
                }
            ],
            "style": "mla"
        }

        result = await research_agent.execute_task(
            task_type="citation_generation",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["style"] == "mla"

    @pytest.mark.asyncio
    async def test_citation_generation_multiple_sources(self, research_agent):
        """Test citation generation with multiple sources."""
        request = {
            "sources": [
                {"title": "Source 1", "url": "https://example1.com"},
                {"title": "Source 2", "url": "https://example2.com"},
                {"title": "Source 3", "url": "https://example3.com"}
            ],
            "style": "chicago"
        }

        result = await research_agent.execute_task(
            task_type="citation_generation",
            input_data=request
        )

        assert result["status"] == "completed"
        assert len(result["citations"]) == 3


class TestLiteratureReview:
    """Test literature review functionality."""

    @pytest.mark.asyncio
    async def test_literature_review_success(self, research_agent):
        """Test successful literature review."""
        request = {
            "topic": "machine learning in healthcare",
            "timeframe": "3years",
            "databases": ["pubmed", "ieee"]
        }

        # Mock academic paper search
        research_agent._search_academic_papers = AsyncMock(return_value=[
            {
                "title": "ML in Medical Diagnosis",
                "authors": ["Dr. A", "Dr. B"],
                "year": 2023,
                "citations": 45
            }
        ])

        result = await research_agent.execute_task(
            task_type="literature_review",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["topic"] == request["topic"]
        assert "papers_reviewed" in result
        assert "categories" in result
        assert "trends" in result
        assert "research_gaps" in result
        assert "synthesis" in result

    @pytest.mark.asyncio
    async def test_literature_review_default_params(self, research_agent):
        """Test literature review with default parameters."""
        request = {
            "topic": "artificial intelligence ethics"
        }

        research_agent._search_academic_papers = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="literature_review",
            input_data=request
        )

        assert result["status"] == "completed"


class TestTrendAnalysis:
    """Test trend analysis functionality."""

    @pytest.mark.asyncio
    async def test_trend_analysis_success(self, research_agent):
        """Test successful trend analysis."""
        request = {
            "topic": "electric vehicles",
            "time_period": "2years",
            "sources": ["news", "academic"]
        }

        # Mock temporal data collection
        research_agent._collect_temporal_data = AsyncMock(return_value=[
            {
                "date": datetime.utcnow() - timedelta(days=30),
                "mentions": 150,
                "sentiment": 0.7
            }
        ])

        result = await research_agent.execute_task(
            task_type="trend_analysis",
            input_data=request
        )

        assert result["status"] == "completed"
        assert result["topic"] == request["topic"]
        assert "trends" in result
        assert "predictions" in result
        assert "insights" in result

    @pytest.mark.asyncio
    async def test_trend_analysis_default_params(self, research_agent):
        """Test trend analysis with default parameters."""
        request = {
            "topic": "cryptocurrency adoption"
        }

        research_agent._collect_temporal_data = AsyncMock(return_value=[])

        result = await research_agent.execute_task(
            task_type="trend_analysis",
            input_data=request
        )

        assert result["status"] == "completed"


class TestHelperMethods:
    """Test internal helper methods."""

    @pytest.mark.asyncio
    async def test_calculate_relevance(self, research_agent):
        """Test relevance calculation."""
        content = "artificial intelligence machine learning deep learning"
        query = "artificial intelligence"

        relevance = await research_agent._calculate_relevance(content, query)

        assert 0 <= relevance <= 1
        assert relevance > 0  # Should have some relevance

    @pytest.mark.asyncio
    async def test_assess_credibility(self, research_agent):
        """Test credibility assessment."""
        # High credibility source
        academic_source = {
            "url": "https://arxiv.org/paper",
            "source_type": "academic"
        }

        credibility = await research_agent._assess_credibility(academic_source)
        assert credibility == CredibilityLevel.HIGH

        # Medium credibility source
        wiki_source = {
            "url": "https://wikipedia.org/article",
            "source_type": "web"
        }

        credibility = await research_agent._assess_credibility(wiki_source)
        assert credibility == CredibilityLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_generate_summary(self, research_agent):
        """Test content summarization."""
        content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."

        summary = await research_agent._generate_summary(content)

        assert len(summary) > 0
        assert len(summary) <= len(content)

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, research_agent):
        """Test confidence score calculation."""
        sources = [
            ResearchSource(
                url="https://example1.com",
                title="Source 1",
                credibility=CredibilityLevel.HIGH,
                relevance_score=0.9
            ),
            ResearchSource(
                url="https://example2.com",
                title="Source 2",
                credibility=CredibilityLevel.MEDIUM,
                relevance_score=0.7
            )
        ]

        confidence = await research_agent._calculate_confidence_score(sources)

        assert 0 <= confidence <= 1

    @pytest.mark.asyncio
    async def test_format_citation_apa(self, research_agent):
        """Test APA citation formatting."""
        source = ResearchSource(
            url="https://journal.com/paper",
            title="Research Paper Title",
            author="Dr. Smith",
            publication_date=datetime(2024, 1, 1)
        )

        citation = await research_agent._format_citation(source, CitationStyle.APA)

        assert "Dr. Smith" in citation
        assert "2024" in citation
        assert "Research Paper Title" in citation

    @pytest.mark.asyncio
    async def test_format_citation_mla(self, research_agent):
        """Test MLA citation formatting."""
        source = ResearchSource(
            url="https://example.com/article",
            title="Article Title",
            author="Jane Doe"
        )

        citation = await research_agent._format_citation(source, CitationStyle.MLA)

        assert "Jane Doe" in citation
        assert "Article Title" in citation


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_unsupported_task_type(self, research_agent):
        """Test handling of unsupported task types."""
        with pytest.raises(ValidationError):
            await research_agent.execute_task(
                task_type="unsupported_task",
                input_data={}
            )

    @pytest.mark.asyncio
    async def test_empty_research_query(self, research_agent):
        """Test handling of empty research query."""
        request = {
            "query": "",
            "research_type": "academic"
        }

        with pytest.raises(ValidationError):
            await research_agent.execute_task(
                task_type="research_query",
                input_data=request
            )

    @pytest.mark.asyncio
    async def test_invalid_research_type(self, research_agent):
        """Test handling of invalid research type."""
        request = {
            "query": "valid query",
            "research_type": "invalid_type"
        }

        with pytest.raises(ValidationError):
            await research_agent.execute_task(
                task_type="research_query",
                input_data=request
            )

    @pytest.mark.asyncio
    async def test_network_error_handling(self, research_agent):
        """Test handling of network errors during research."""
        research_agent._search_sources = AsyncMock(
            side_effect=Exception("Network error")
        )

        with pytest.raises(AgentExecutionError):
            await research_agent.execute_task(
                task_type="research_query",
                input_data={"query": "test query", "research_type": "academic"}
            )


class TestDataStructures:
    """Test data structure validation and functionality."""

    def test_research_source_creation(self):
        """Test ResearchSource creation and properties."""
        source = ResearchSource(
            url="https://example.com",
            title="Test Source",
            author="Test Author",
            credibility=CredibilityLevel.HIGH,
            relevance_score=0.85
        )

        assert source.url == "https://example.com"
        assert source.title == "Test Source"
        assert source.credibility == CredibilityLevel.HIGH
        assert source.relevance_score == 0.85
        assert source.key_points == []  # Default value

    def test_research_query_creation(self):
        """Test ResearchQuery creation with defaults."""
        query = ResearchQuery(
            query="test query",
            research_type=ResearchType.ACADEMIC
        )

        assert query.query == "test query"
        assert query.research_type == ResearchType.ACADEMIC
        assert query.depth == ResearchDepth.STANDARD  # Default
        assert query.max_sources == 20  # Default
        assert query.domains == []  # Default
        assert query.languages == ["en"]  # Default

    def test_research_request_validation(self):
        """Test ResearchRequest validation."""
        # Valid request
        request = ResearchRequest(
            query="valid query",
            research_type=ResearchType.MARKET
        )
        assert request.query == "valid query"

        # Invalid query (too short)
        with pytest.raises(ValueError):
            ResearchRequest(
                query="AB",  # Too short
                research_type=ResearchType.ACADEMIC
            )

    def test_document_analysis_request_validation(self):
        """Test DocumentAnalysisRequest validation."""
        # Valid request with content
        request = DocumentAnalysisRequest(
            document_content="Valid content",
            document_format=DocumentFormat.TXT
        )
        assert request.document_content == "Valid content"

        # Valid request with URL
        request = DocumentAnalysisRequest(
            document_url="https://example.com/doc.pdf",
            document_format=DocumentFormat.PDF
        )
        assert str(request.document_url) == "https://example.com/doc.pdf"

        # Invalid request (neither content nor URL)
        with pytest.raises(ValueError):
            DocumentAnalysisRequest(
                document_format=DocumentFormat.PDF
            )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
