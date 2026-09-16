"""initial schema: parties, party_members, party_member_moves

Revision ID: 0001
Revises:
Create Date: 2026-09-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parties",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "party_members",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "party_id",
            sa.Integer,
            sa.ForeignKey("parties.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("species_id", sa.Integer, nullable=False),
        sa.Column("species_name", sa.String(100), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("item", sa.String(100), nullable=True),
        sa.Column("ability", sa.String(100), nullable=True),
        sa.Column("nature", sa.String(20), nullable=False),
        sa.Column("ev_hp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ev_attack", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ev_defense", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ev_special_attack", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ev_special_defense", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ev_speed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("iv_hp", sa.Integer, nullable=False, server_default="31"),
        sa.Column("iv_attack", sa.Integer, nullable=False, server_default="31"),
        sa.Column("iv_defense", sa.Integer, nullable=False, server_default="31"),
        sa.Column("iv_special_attack", sa.Integer, nullable=False, server_default="31"),
        sa.Column("iv_special_defense", sa.Integer, nullable=False, server_default="31"),
        sa.Column("iv_speed", sa.Integer, nullable=False, server_default="31"),
    )
    op.create_index("ix_party_members_party_id", "party_members", ["party_id"])

    op.create_table(
        "party_member_moves",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "party_member_id",
            sa.Integer,
            sa.ForeignKey("party_members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("move_slot", sa.Integer, nullable=False),
        sa.Column("move_id", sa.Integer, nullable=False),
        sa.Column("move_name", sa.String(100), nullable=False),
    )
    op.create_index(
        "ix_party_member_moves_party_member_id", "party_member_moves", ["party_member_id"]
    )


def downgrade() -> None:
    op.drop_table("party_member_moves")
    op.drop_table("party_members")
    op.drop_table("parties")
