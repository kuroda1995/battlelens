from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Party(Base):
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["PartyMember"]] = relationship(
        back_populates="party", cascade="all, delete-orphan", order_by="PartyMember.position"
    )


class PartyMember(Base):
    __tablename__ = "party_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)  # 1-6

    species_id: Mapped[int] = mapped_column(Integer)
    species_name: Mapped[str] = mapped_column(String(100))
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ability: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nature: Mapped[str] = mapped_column(String(20))

    ev_hp: Mapped[int] = mapped_column(Integer, default=0)
    ev_attack: Mapped[int] = mapped_column(Integer, default=0)
    ev_defense: Mapped[int] = mapped_column(Integer, default=0)
    ev_special_attack: Mapped[int] = mapped_column(Integer, default=0)
    ev_special_defense: Mapped[int] = mapped_column(Integer, default=0)
    ev_speed: Mapped[int] = mapped_column(Integer, default=0)

    iv_hp: Mapped[int] = mapped_column(Integer, default=31)
    iv_attack: Mapped[int] = mapped_column(Integer, default=31)
    iv_defense: Mapped[int] = mapped_column(Integer, default=31)
    iv_special_attack: Mapped[int] = mapped_column(Integer, default=31)
    iv_special_defense: Mapped[int] = mapped_column(Integer, default=31)
    iv_speed: Mapped[int] = mapped_column(Integer, default=31)

    party: Mapped["Party"] = relationship(back_populates="members")
    moves: Mapped[list["PartyMemberMove"]] = relationship(
        back_populates="party_member",
        cascade="all, delete-orphan",
        order_by="PartyMemberMove.move_slot",
    )


class PartyMemberMove(Base):
    __tablename__ = "party_member_moves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_member_id: Mapped[int] = mapped_column(
        ForeignKey("party_members.id", ondelete="CASCADE")
    )
    move_slot: Mapped[int] = mapped_column(Integer)  # 1-4
    move_id: Mapped[int] = mapped_column(Integer)
    move_name: Mapped[str] = mapped_column(String(100))

    party_member: Mapped["PartyMember"] = relationship(back_populates="moves")
