"""Policy configuration repository — scanner enable/disable and sensitivity."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import PolicyConfig

DEFAULT_SCANNERS = [
    "data_protection",
    "content_guard",
]


class PolicyConfigRepository:
    @staticmethod
    async def list_policies(session: AsyncSession) -> list[PolicyConfig]:
        result = await session.execute(select(PolicyConfig))
        policies = list(result.scalars().all())
        if not policies:
            # Seed defaults on first access
            for name in DEFAULT_SCANNERS:
                p = PolicyConfig(scanner_name=name, enabled=True, sensitivity="medium")
                session.add(p)
            await session.commit()
            result = await session.execute(select(PolicyConfig))
            policies = list(result.scalars().all())
        return policies

    @staticmethod
    async def update_policy(session: AsyncSession, scanner_name: str,
                            enabled: bool, sensitivity: str) -> PolicyConfig | None:
        result = await session.execute(
            select(PolicyConfig).where(PolicyConfig.scanner_name == scanner_name)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            return None
        policy.enabled = enabled
        policy.sensitivity = sensitivity
        await session.commit()
        await session.refresh(policy)
        return policy
