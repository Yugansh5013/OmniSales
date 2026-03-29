"""Kafka event schemas — Pydantic models for all inter-agent events."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event with common fields."""
    org_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Closer Events ──


class DealWonEvent(BaseEvent):
    """Published when a deal is closed-won."""
    deal_id: str
    account_id: str
    arr: float  # annual recurring revenue


class DealLostEvent(BaseEvent):
    """Published when a deal is lost."""
    deal_id: str
    reason: str


# ── Prospector Events ──


class LeadQualifiedEvent(BaseEvent):
    """Published when a lead passes ICP scoring."""
    lead_id: str
    company: str
    contact: str
    icp_score: float  # 0–1
    tier: str  # A, B, C, D


# ── Guardian Events ──


class ChurnRiskEvent(BaseEvent):
    """Published when high churn risk is detected."""
    account_id: str
    churn_risk: float  # 0–1
    reason: str
    competitor: Optional[str] = None
    top_signals: list[str] = Field(default_factory=list)


class UpsellOpportunityEvent(BaseEvent):
    """Published when an upsell opportunity is detected."""
    account_id: str
    current_plan: str
    usage_pct: float
    recommended_plan: str


# ── Spy Events ──


class CompetitorEvent(BaseEvent):
    """Published when a competitor change is detected."""
    competitor: str
    event_type: str  # price_increase, new_feature, downtime, etc.
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    source_url: Optional[str] = None


# ── Topic Registry ──

TOPICS = {
    "closer.deal_won": DealWonEvent,
    "closer.deal_lost": DealLostEvent,
    "prospector.lead_qualified": LeadQualifiedEvent,
    "guardian.churn_risk": ChurnRiskEvent,
    "guardian.upsell_opportunity": UpsellOpportunityEvent,
    "spy.competitor_event": CompetitorEvent,
}
