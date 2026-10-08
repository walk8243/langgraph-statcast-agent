"""Multi-stage orchestration pipeline connecting interactive desk planning to article generation."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional, Tuple

from src.article_desk_agent import ArticleDeskAgent, DeskAgentResponse, DeskPlanProposal
from src.multi_article_service import MultiArticleService
from src.postgres_client import Article

logger = logging.getLogger(__name__)


class OrchestrationPipeline:
    """End-to-end pipeline coordinating desk planning and multi-material article synthesis."""

    def __init__(
        self,
        desk_agent: Optional[ArticleDeskAgent] = None,
        multi_article_service: Optional[MultiArticleService] = None,
    ):
        self.desk_agent = desk_agent or ArticleDeskAgent()
        self.multi_service = multi_article_service or MultiArticleService()

    def generate_article_from_proposal(
        self,
        proposal: DeskPlanProposal,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Article:
        """Execute multi-material gathering and article writing from a finalized proposal."""
        outline, requirements = proposal.to_outline_and_requirements()

        if progress_callback:
            progress_callback("素材収集開始", 0, len(requirements))

        logger.info(
            f"Executing article generation for proposal '{proposal.title}' ({len(requirements)} materials)"
        )
        article = self.multi_service.generate_and_save_multi_article(outline, requirements)

        if progress_callback:
            progress_callback("記事生成完了", len(requirements), len(requirements))

        return article

    def process_chat_and_run(
        self,
        messages: List[Dict[str, str]],
        auto_generate_on_finalize: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[DeskAgentResponse, Optional[Article]]:
        """Run one conversational turn with DeskAgent, and optionally generate article if finalized.

        Returns:
            Tuple of (DeskAgentResponse, Optional[Article])
        """
        desk_response = self.desk_agent.chat(messages)

        article: Optional[Article] = None
        if (
            auto_generate_on_finalize
            and desk_response.is_finalized
            and desk_response.proposal
            and desk_response.proposal.requirements
        ):
            logger.info("Proposal is finalized. Automatically launching article generation pipeline.")
            article = self.generate_article_from_proposal(
                desk_response.proposal,
                progress_callback=progress_callback,
            )

        return desk_response, article
