"""Payment Card API endpoints.

This module provides REST API endpoints for managing payment cards
and getting balance summaries.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.models.payment_card import PaymentCard
from src.schemas.payment_card import (
    AllCardsBalanceSummary,
    FundingCardInfo,
    PaymentCardCreate,
    PaymentCardResponse,
    PaymentCardUpdate,
)
from src.security.rate_limit import limiter, rate_limit_get, rate_limit_write
from src.services.currency_service import CurrencyService
from src.services.payment_card_service import PaymentCardService


def _card_to_response(card: PaymentCard) -> PaymentCardResponse:
    """Convert a PaymentCard model to response, handling lazy-loaded funding_card."""
    funding_card_info = None
    if card.funding_card:
        funding_card_info = FundingCardInfo(
            id=card.funding_card.id,
            name=card.funding_card.name,
            color=card.funding_card.color,
            icon_url=card.funding_card.icon_url,
        )

    return PaymentCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        last_four=card.last_four,
        bank_name=card.bank_name,
        currency=card.currency,
        color=card.color,
        icon_url=card.icon_url,
        notes=card.notes,
        sort_order=card.sort_order,
        funding_card_id=card.funding_card_id,
        is_active=card.is_active,
        funding_card=funding_card_info,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


router = APIRouter(prefix="/cards", tags=["Payment Cards"])


@router.post(
    "",
    response_model=PaymentCardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create payment card",
    description="Create a new payment card/account for tracking payments.",
)
@limiter.limit(rate_limit_write)
async def create_card(
    request: Request,
    data: PaymentCardCreate,
    db: AsyncSession = Depends(get_db),
) -> PaymentCardResponse:
    """Create a new payment card."""
    service = PaymentCardService(db)
    card = await service.create(data)
    await db.commit()
    return _card_to_response(card)


@router.get(
    "",
    response_model=list[PaymentCardResponse],
    summary="List payment cards",
    description="Get all payment cards, optionally filtered by active status.",
)
@limiter.limit(rate_limit_get)
async def list_cards(
    request: Request,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentCardResponse]:
    """List all payment cards."""
    service = PaymentCardService(db)
    cards = await service.get_all(is_active=is_active)
    return [_card_to_response(card) for card in cards]


@router.get(
    "/balance-summary",
    response_model=AllCardsBalanceSummary,
    summary="Get card balance summary",
    description="Get summary of required balances for all cards based on subscriptions.",
)
@limiter.limit(rate_limit_get)
async def get_balance_summary(
    request: Request,
    currency: str = "GBP",
    db: AsyncSession = Depends(get_db),
) -> AllCardsBalanceSummary:
    """Get balance summary for all cards."""
    service = PaymentCardService(db)
    currency_service = CurrencyService()
    return await service.get_balance_summary(
        currency_service=currency_service,
        target_currency=currency,
    )


@router.get(
    "/{card_id}",
    response_model=PaymentCardResponse,
    summary="Get payment card",
    description="Get a payment card by ID.",
)
@limiter.limit(rate_limit_get)
async def get_card(
    request: Request,
    card_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaymentCardResponse:
    """Get a payment card by ID."""
    service = PaymentCardService(db)
    card = await service.get_by_id(card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    return _card_to_response(card)


@router.patch(
    "/{card_id}",
    response_model=PaymentCardResponse,
    summary="Update payment card",
    description="Update a payment card's details.",
)
@limiter.limit(rate_limit_write)
async def update_card(
    request: Request,
    card_id: str,
    data: PaymentCardUpdate,
    db: AsyncSession = Depends(get_db),
) -> PaymentCardResponse:
    """Update a payment card."""
    service = PaymentCardService(db)
    card = await service.update(card_id, data)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    await db.commit()
    # Re-fetch with funding_card loaded after commit
    card = await service.get_by_id(card_id)
    return _card_to_response(card)


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete payment card",
    description="Delete a payment card. Subscriptions using this card will have card_id set to null.",
)
@limiter.limit(rate_limit_write)
async def delete_card(
    request: Request,
    card_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a payment card."""
    service = PaymentCardService(db)
    deleted = await service.delete(card_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    await db.commit()
