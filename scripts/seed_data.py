"""Seed database with sample data."""

import asyncio
from datetime import date
from decimal import Decimal

from src.db.database import async_session_maker, init_db
from src.models.subscription import Frequency, Subscription

SAMPLE_SUBSCRIPTIONS = [
    {
        "name": "Netflix",
        "amount": Decimal("15.99"),
        "frequency": Frequency.MONTHLY,
        "category": "Entertainment",
        "start_date": date(2023, 1, 15),
    },
    {
        "name": "Gym Membership",
        "amount": Decimal("49.99"),
        "frequency": Frequency.MONTHLY,
        "category": "Health",
        "start_date": date(2023, 3, 1),
    },
    {
        "name": "Therapy Sessions",
        "amount": Decimal("150.00"),
        "frequency": Frequency.BIWEEKLY,
        "category": "Health",
        "start_date": date(2023, 6, 1),
    },
    {
        "name": "Car Insurance",
        "amount": Decimal("600.00"),
        "frequency": Frequency.QUARTERLY,
        "category": "Insurance",
        "start_date": date(2023, 1, 1),
    },
    {
        "name": "Spotify Family",
        "amount": Decimal("16.99"),
        "frequency": Frequency.MONTHLY,
        "category": "Entertainment",
        "start_date": date(2022, 8, 20),
    },
]


async def seed() -> None:
    """Seed the database with sample data."""
    await init_db()

    async with async_session_maker() as session:
        for data in SAMPLE_SUBSCRIPTIONS:
            sub = Subscription(
                **data,
                next_payment_date=data["start_date"],
            )
            session.add(sub)

        await session.commit()
        print(f"✅ Seeded {len(SAMPLE_SUBSCRIPTIONS)} subscriptions")


if __name__ == "__main__":
    asyncio.run(seed())
