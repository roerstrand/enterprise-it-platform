from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.ci_model import ConfigurationItemModel
from data.models.relationship_model import CIRelationshipModel
from data.models.team_model import TeamModel

async def create_ci_in_db(db: AsyncSession, name: str, ci_type: str, environment: str, owner_team_id: int | None = None, owner_user_id: int | None = None):
    ci = ConfigurationItemModel(name=name, ci_type=ci_type, environment=environment, owner_team_id=owner_team_id, owner_user_id=owner_user_id)
    db.add(ci)
    await db.commit()
    return ci

async def get_ci_by_id_from_db(db: AsyncSession, ci_id: int):
    result = await db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id == ci_id)
    )
    return result.scalars().first()

async def get_all_cis_from_db(db: AsyncSession):
    result = await db.execute(select(ConfigurationItemModel))
    return result.scalars().all()

async def create_relationship_in_db(db: AsyncSession, source_ci_id: int, target_ci_id: int, relationship_type: str):
    relationship = CIRelationshipModel(
        source_ci_id=source_ci_id,
        target_ci_id=target_ci_id,
        relationship_type=relationship_type,
    )
    db.add(relationship)
    await db.commit()
    return relationship

async def get_related_cis_from_db(db: AsyncSession, ci_id: int):
    result = await db.execute(
        select(CIRelationshipModel).where(
            or_(
                CIRelationshipModel.source_ci_id == ci_id,
                CIRelationshipModel.target_ci_id == ci_id,
            )
        )
    )
    relationships = result.scalars().all()

    related_ids = {
        r.target_ci_id if r.source_ci_id == ci_id else r.source_ci_id
        for r in relationships
    }
    if not related_ids:
        return []

    result = await db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id.in_(related_ids))
    )
    return result.scalars().all()

async def update_ci_in_db(db: AsyncSession, ci_id: int, name: str, ci_type: str, environment: str, owner_team_id: int | None = None, owner_user_id: int | None = None):
    result = await db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id == ci_id)
    )
    ci = result.scalars().first()
    if ci: 
        ci.name = name
        ci.ci_type = ci_type
        ci.environment = environment
        ci.owner_team_id = owner_team_id
        ci.owner_user_id = owner_user_id
        await db.commit()
    return ci

async def delete_ci_from_db(db: AsyncSession, ci_id: int):
    result = await db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id == ci_id)
    )
    ci = result.scalars().first()
    if not ci:
        return False
    await db.delete(ci)
    await db.commit()
    return True
