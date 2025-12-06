"""
Report Indexing Service for RAG
Indexes saved report content into ChromaDB for conversational queries
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import json

from app.services.vector_store import vector_store_service
from app.rag.document_processor import TextChunker


class ReportIndexingService:
    """Service for indexing report content into RAG"""

    @staticmethod
    def _extract_report_sections(report_content: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract meaningful text sections from report JSON

        Args:
            report_content: Report JSON structure with agent results

        Returns:
            List of dicts with 'section' name and 'text' content
        """
        sections = []

        # Extract availability agent section
        if "availability_agent" in report_content:
            availability = report_content["availability_agent"]
            text_parts = [
                "=== ENERGY AVAILABILITY ANALYSIS ===\n",
                f"Confidence: {availability.get('confidence', 'N/A')}\n",
            ]

            if "results" in availability:
                results = availability["results"]
                if isinstance(results, dict):
                    text_parts.append(f"\nResults:\n{json.dumps(results, indent=2)}")
                else:
                    text_parts.append(f"\nResults: {results}")

            if "reasoning" in availability:
                text_parts.append(f"\nReasoning:\n{availability['reasoning']}")

            if "sources" in availability:
                sources = availability.get("sources", [])
                if sources:
                    text_parts.append(f"\nData Sources: {', '.join(sources)}")

            sections.append({
                "section": "availability_agent",
                "text": "\n".join(text_parts)
            })

        # Extract optimization agent section
        if "optimization_agent" in report_content:
            optimization = report_content["optimization_agent"]
            text_parts = [
                "=== PRICE OPTIMIZATION ANALYSIS ===\n",
                f"Confidence: {optimization.get('confidence', 'N/A')}\n",
            ]

            if "results" in optimization:
                results = optimization["results"]
                if isinstance(results, dict):
                    text_parts.append(f"\nResults:\n{json.dumps(results, indent=2)}")
                else:
                    text_parts.append(f"\nResults: {results}")

            if "reasoning" in optimization:
                text_parts.append(f"\nReasoning:\n{optimization['reasoning']}")

            if "sources" in optimization:
                sources = optimization.get("sources", [])
                if sources:
                    text_parts.append(f"\nData Sources: {', '.join(sources)}")

            sections.append({
                "section": "optimization_agent",
                "text": "\n".join(text_parts)
            })

        # Extract portfolio agent section (most detailed)
        if "portfolio_agent" in report_content:
            portfolio = report_content["portfolio_agent"]
            text_parts = [
                "=== ENERGY PORTFOLIO RECOMMENDATIONS ===\n",
                f"Confidence: {portfolio.get('confidence', 'N/A')}\n",
            ]

            # Portfolio mix
            if "portfolio" in portfolio:
                portfolio_mix = portfolio["portfolio"]
                text_parts.append("\nRecommended Energy Portfolio Mix:")
                if isinstance(portfolio_mix, dict):
                    for source, percentage in portfolio_mix.items():
                        text_parts.append(f"  - {source}: {percentage}")
                else:
                    text_parts.append(f"{portfolio_mix}")

            # ESG scores
            if "esg_scores" in portfolio:
                esg = portfolio["esg_scores"]
                text_parts.append("\nESG Impact Scores:")
                if isinstance(esg, dict):
                    for metric, score in esg.items():
                        text_parts.append(f"  - {metric}: {score}")
                else:
                    text_parts.append(f"{esg}")

            # Transition roadmap
            if "transition_roadmap" in portfolio:
                roadmap = portfolio["transition_roadmap"]
                text_parts.append("\nTransition Roadmap:")
                if isinstance(roadmap, list):
                    for idx, phase in enumerate(roadmap, 1):
                        text_parts.append(f"\nPhase {idx}:")
                        if isinstance(phase, dict):
                            for key, value in phase.items():
                                text_parts.append(f"  {key}: {value}")
                        else:
                            text_parts.append(f"  {phase}")
                else:
                    text_parts.append(f"{roadmap}")

            if "results" in portfolio:
                results = portfolio["results"]
                if isinstance(results, dict):
                    text_parts.append(f"\nDetailed Results:\n{json.dumps(results, indent=2)}")
                elif results:
                    text_parts.append(f"\nResults: {results}")

            if "reasoning" in portfolio:
                text_parts.append(f"\nReasoning:\n{portfolio['reasoning']}")

            if "sources" in portfolio:
                sources = portfolio.get("sources", [])
                if sources:
                    text_parts.append(f"\nData Sources: {', '.join(sources)}")

            sections.append({
                "section": "portfolio_agent",
                "text": "\n".join(text_parts)
            })

        # Extract overall summary
        summary_parts = []
        if "overall_confidence" in report_content:
            summary_parts.append(f"Overall Report Confidence: {report_content['overall_confidence']}")

        if "reasoning_chain" in report_content:
            chain = report_content["reasoning_chain"]
            if chain:
                summary_parts.append("\nReasoning Chain:")
                if isinstance(chain, list):
                    for step in chain:
                        summary_parts.append(f"  - {step}")
                else:
                    summary_parts.append(f"{chain}")

        if "agents_involved" in report_content:
            agents = report_content["agents_involved"]
            if agents:
                summary_parts.append(f"\nAgents Involved: {', '.join(agents)}")

        if summary_parts:
            sections.append({
                "section": "summary",
                "text": "=== REPORT SUMMARY ===\n" + "\n".join(summary_parts)
            })

        return sections

    async def index_report(
        self,
        report_id: int,
        report_name: str,
        report_content: Dict[str, Any],
        profile_snapshot: Dict[str, Any],
        user_id: int,
        provider: str = "custom"
    ) -> bool:
        """
        Index a saved report into ChromaDB

        Args:
            report_id: ID of the saved report
            report_name: Name of the report
            report_content: Full report JSON content
            profile_snapshot: Profile data snapshot
            user_id: User ID who owns the report
            provider: LLM provider for embeddings

        Returns:
            True if indexing succeeded, False otherwise
        """
        try:
            logger.info(f"Starting indexing for report {report_id} ('{report_name}')")

            # Extract sections from report
            sections = self._extract_report_sections(report_content)

            if not sections:
                logger.warning(f"No extractable content found in report {report_id}")
                return False

            # Prepare profile context for metadata
            profile_context = {
                "industry": profile_snapshot.get("industry", "Unknown"),
                "location": profile_snapshot.get("location", "Unknown"),
                "company_name": profile_snapshot.get("company_name", "Unknown")
            }

            # Prepare documents and metadata for indexing
            texts = []
            metadatas = []

            for section in sections:
                # Add context header to each section
                context_header = f"Report: {report_name}\n"
                context_header += f"Company: {profile_context['company_name']}\n"
                context_header += f"Industry: {profile_context['industry']}\n"
                context_header += f"Location: {profile_context['location']}\n\n"

                full_text = context_header + section["text"]

                # Chunk the text if it's too large
                # Use smaller chunks for reports to maintain context
                chunks = TextChunker.chunk_text(
                    text=full_text,
                    chunk_size=800,
                    chunk_overlap=150
                )

                for chunk_data in chunks:
                    texts.append(chunk_data["text"])
                    metadatas.append({
                        "report_id": str(report_id),
                        "report_name": report_name,
                        "section": section["section"],
                        "content_type": "energy_report",
                        "industry": profile_context["industry"],
                        "location": profile_context["location"],
                        "company_name": profile_context["company_name"],
                        "chunk_index": chunk_data.get("chunk_index", 0)
                    })

            # Add to vector store with company scope
            # This makes the report data available for RAG queries
            await vector_store_service.add_documents(
                texts=texts,
                metadatas=metadatas,
                provider=provider,
                scope="company",  # Company-scoped so it's available for the user
                user_id=user_id
            )

            logger.info(
                f"Successfully indexed report {report_id} with {len(texts)} chunks "
                f"across {len(sections)} sections"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to index report {report_id}: {e}")
            return False

    async def remove_report_from_index(
        self,
        report_id: int,
        user_id: int,
        provider: str = "custom"
    ) -> bool:
        """
        Remove a report's content from ChromaDB

        Args:
            report_id: ID of the report to remove
            user_id: User ID
            provider: LLM provider

        Returns:
            True if removal succeeded, False otherwise
        """
        try:
            logger.info(f"Removing report {report_id} from index")

            # Delete documents with matching report_id from company collection
            await vector_store_service.delete_by_metadata(
                filter_metadata={"report_id": str(report_id)},
                provider=provider,
                scope="company",
                user_id=user_id
            )

            logger.info(f"Successfully removed report {report_id} from index")
            return True

        except Exception as e:
            logger.error(f"Failed to remove report {report_id} from index: {e}")
            return False


# Singleton instance
report_indexing_service = ReportIndexingService()
