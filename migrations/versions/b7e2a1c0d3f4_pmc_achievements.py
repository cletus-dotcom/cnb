"""pmc achievements

Revision ID: b7e2a1c0d3f4
Revises: 163d704fdb44
Create Date: 2026-04-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7e2a1c0d3f4"
down_revision = "163d704fdb44"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pmc_achievements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.String(length=800), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("pmc_achievements", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_pmc_achievements_fiscal_year"), ["fiscal_year"], unique=False
        )


def downgrade():
    with op.batch_alter_table("pmc_achievements", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pmc_achievements_fiscal_year"))

    op.drop_table("pmc_achievements")
