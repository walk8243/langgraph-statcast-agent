"""FastAPI server for MLB Statcast Article Generator Service."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src.article_desk_agent import ArticleDeskAgent
from src.multi_article_service import MultiArticleService
from src.multi_article_synthesizer import (
    ArticleOutline,
    ArticleOutlineSection,
    DataRequirement,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("article-generator-api")

app = FastAPI(
    title="Statcast Article Generator API",
    description="REST API for Editorial Desk Agent and Multi-material Article Generation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class DeskChatRequest(BaseModel):
    messages: list[ChatMessage]


class SectionModel(BaseModel):
    title: str
    description: str
    material_label: Optional[str] = None


class RequirementModel(BaseModel):
    label: str
    prompt: str
    section_hint: Optional[str] = None


class ProposalModel(BaseModel):
    title: str
    theme: str
    sections: list[SectionModel] = Field(default_factory=list)
    requirements: list[RequirementModel] = Field(default_factory=list)


class DeskChatResponse(BaseModel):
    reply: str
    is_finalized: bool
    proposal: Optional[ProposalModel] = None


class DeskGenerateRequest(BaseModel):
    proposal: ProposalModel


class DeskGenerateResponse(BaseModel):
    success: bool
    article_id: int
    title: str
    model_name: Optional[str] = None


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post(
    "/api/desk/chat",
    response_model=DeskChatResponse,
    tags=["Desk Agent"],
    summary="Chat turn with Editorial Desk Agent",
)
def desk_chat(request: DeskChatRequest) -> DeskChatResponse:
    """Run a conversational turn with the Editorial Desk Agent."""
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty",
        )

    try:
        agent = ArticleDeskAgent()
        # Convert Pydantic models to dicts for agent.chat()
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        res = agent.chat(chat_history)

        proposal_data: Optional[ProposalModel] = None
        if res.proposal:
            proposal_data = ProposalModel(
                title=res.proposal.title,
                theme=res.proposal.theme,
                sections=[
                    SectionModel(
                        title=s.title,
                        description=s.description,
                        material_label=s.material_label,
                    )
                    for s in res.proposal.sections
                ],
                requirements=[
                    RequirementModel(
                        label=r.label,
                        prompt=r.prompt,
                        section_hint=r.section_hint,
                    )
                    for r in res.proposal.requirements
                ],
            )

        return DeskChatResponse(
            reply=res.reply,
            is_finalized=res.is_finalized,
            proposal=proposal_data,
        )
    except Exception as e:
        logger.error("Desk agent chat error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Desk agent execution failed: {e}",
        ) from e


@app.post(
    "/api/desk/generate",
    response_model=DeskGenerateResponse,
    tags=["Article Generation"],
    summary="Generate multi-material article from proposal",
)
def desk_generate(request: DeskGenerateRequest) -> DeskGenerateResponse:
    """Generate and persist multi-material article to PostgreSQL."""
    prop = request.proposal
    if not prop.requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one data requirement is needed to generate article",
        )

    try:
        sections = [
            ArticleOutlineSection(
                title=s.title,
                description=s.description,
                material_label=s.material_label,
            )
            for s in prop.sections
        ]
        outline = ArticleOutline(
            title=prop.title,
            theme=prop.theme,
            sections=sections,
        )

        requirements = [
            DataRequirement(
                label=r.label,
                prompt=r.prompt,
                section_hint=r.section_hint,
            )
            for r in prop.requirements
        ]

        service = MultiArticleService()
        article = service.generate_and_save_multi_article(outline, requirements)

        return DeskGenerateResponse(
            success=True,
            article_id=article.id,
            title=article.title,
            model_name=article.model_name,
        )
    except Exception as e:
        logger.error("Article generation failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Article generation failed: {e}",
        ) from e


def run_server(host: str = "0.0.0.0", port: int = 8002) -> None:
    """Start uvicorn server."""
    logger.info("Starting Article Generator API server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    port_env = int(os.environ.get("PORT", "8002"))
    host_env = os.environ.get("HOST", "0.0.0.0")
    run_server(host=host_env, port=port_env)
