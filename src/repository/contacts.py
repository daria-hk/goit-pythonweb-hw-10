from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datetime import date, timedelta

from src.database.models import Contact, User
from src.schemas import ContactBase, ContactUpdate


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User, query: str | None = None) -> List[Contact]:
        stmt = (
            select(Contact)
            .filter_by(user=user)
            .offset(skip)
            .limit(limit)
        )

        if query:
            stmt = stmt.where(
                (Contact.first_name.ilike(f"%{query}%"))
                | (Contact.last_name.ilike(f"%{query}%"))
                | (Contact.email.ilike(f"%{query}%"))
            )

        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactBase, user: User) -> Contact:
        contact = Contact(**body.dict(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id, user)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def get_birthdays(self, user: User) -> List[Contact]:
        today = date.today()
        next_seven_days = today + timedelta(days=7)
        stmt = (
            select(Contact)
            .filter_by(user=user)
            .where(Contact.birthday >= today, Contact.birthday <= next_seven_days)
        )
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()