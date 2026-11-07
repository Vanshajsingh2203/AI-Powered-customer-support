from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from uuid import UUID
from app.models.ticket import Ticket

class CategoryService:

    async def create_category(
        self,
        db: AsyncSession,
        category_data: CategoryCreate
    ):
        # Check whether a category with the same name exists,
        # ignoring uppercase and lowercase differences.
        result = await db.execute(
            select(Category).where(
                func.lower(Category.name) == category_data.name.lower()
            )
        )

        existing_category = result.scalar_one_or_none()

        if existing_category:
            raise ValueError("Category with this name already exists")

        category = Category(
            name=category_data.name.strip(),
            description=category_data.description
        )

        db.add(category)
        await db.flush()

        return category
    
    async def get_categories(self, db: AsyncSession):
        result = await db.execute(
        select(Category).order_by(Category.name.asc())
        )

        return result.scalars().all()
    
    async def get_category_by_id(
    self,
    db: AsyncSession,
    category_id: UUID
):
        result = await db.execute(
        select(Category).where(Category.id == category_id)
        )

        return result.scalar_one_or_none()
    
    async def update_category(
    self,
    db: AsyncSession,
    category_id: UUID,
    category_data: CategoryUpdate
):
        category = await self.get_category_by_id(
            db=db,
            category_id=category_id
        )

        if category is None:
            return None

        update_data = category_data.model_dump(exclude_unset=True)

        if not update_data:
            raise ValueError("No fields provided for update")

        if "name" in update_data:
            if update_data["name"] is None:
                raise ValueError("Category name cannot be null")

            update_data["name"] = update_data["name"].strip()

            if len(update_data["name"]) < 2:
                raise ValueError("Category name must contain at least 2 characters")

            result = await db.execute(
                select(Category).where(
                    func.lower(Category.name) == update_data["name"].lower(),
                    Category.id != category_id
                )
            )

            if result.scalar_one_or_none():
                raise ValueError("Category with this name already exists")

        for field, value in update_data.items():
            setattr(category, field, value)

        await db.flush()

        return category
    async def delete_category(
    self,
    db: AsyncSession,
    category_id: UUID
):
        category = await self.get_category_by_id(
            db=db,
            category_id=category_id
        )

        if category is None:
            return None

        ticket_count_result = await db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.category_id == category_id
            )
        )

        ticket_count = ticket_count_result.scalar_one()

        if ticket_count > 0:
            raise ValueError(
                "Cannot delete category because tickets are associated with it"
            )

        await db.delete(category)
        await db.flush()

        return True

category_service = CategoryService()