"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_exams_id', 'exams', ['id'], unique=False)

    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exam_id', sa.Integer(), sa.ForeignKey('exams.id'), nullable=False),
        sa.Column('user_name', sa.String(), nullable=False),
        sa.Column('suspicious', sa.Boolean(), default=False),
        sa.Column('flag_reasons', sa.Text(), nullable=True),
        sa.Column('time_taken', sa.Integer(), nullable=True),
        sa.Column('answers', sa.Text(), nullable=True),
        sa.Column('audit_log', sa.Text(), nullable=True),   # AI-generated explanation
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_submissions_id', 'submissions', ['id'], unique=False)


def downgrade():
    op.drop_index('ix_submissions_id', table_name='submissions')
    op.drop_table('submissions')
    op.drop_index('ix_exams_id', table_name='exams')
    op.drop_table('exams')
