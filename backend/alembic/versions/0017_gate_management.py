"""gate management"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0017_gate_management"
down_revision = "0016_ingest_uniqueness"
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.create_table(
        "control_gates",
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("gate_type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "closed", "transitioning", "maintenance", name="gate_status"),
            nullable=False,
        ),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("location_description", sa.Text(), nullable=True),
        sa.Column("last_operated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("gate_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_control_gates_region_id_regions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_control_gates_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_control_gates")),
        sa.UniqueConstraint("code", name=op.f("uq_control_gates_code")),
    )
    op.create_index(op.f("ix_control_gates_code"), "control_gates", ["code"], unique=False)
    op.create_index(op.f("ix_control_gates_region_id"), "control_gates", ["region_id"], unique=False)
    op.create_index(op.f("ix_control_gates_station_id"), "control_gates", ["station_id"], unique=False)
    op.create_index(op.f("ix_control_gates_status"), "control_gates", ["status"], unique=False)



def downgrade() -> None:
    op.drop_index(op.f("ix_control_gates_status"), table_name="control_gates")
    op.drop_index(op.f("ix_control_gates_station_id"), table_name="control_gates")
    op.drop_index(op.f("ix_control_gates_region_id"), table_name="control_gates")
    op.drop_index(op.f("ix_control_gates_code"), table_name="control_gates")
    op.drop_table("control_gates")
    sa.Enum(name="gate_status").drop(op.get_bind(), checkfirst=True)
