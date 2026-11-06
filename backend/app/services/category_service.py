from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate


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


category_service = CategoryService()