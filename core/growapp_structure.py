"""
Module to describe the structure of the GrowApp database from PurpleCrane.
Each Class, defines a table in the database.
    __tablename__: creates the table with the name given
    __table_args__: table arguments eg: __table_args__ = {'sqlite_autoincrement': True}
    BASE: the declarative_base() callable returns a new base class from which all mapped classes
    should inherit. When the class definition is completed, a new Table and mapper() is generated.
"""

import uuid
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Column,
    Integer,
    Float,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID

from flask_sqlalchemy import SQLAlchemy

from .constants import SQL_ENGINE

SQLA = SQLAlchemy()
BASE = SQLA.Model


class TrayTypeClass(BASE):
    """
    A list of all the possible types of tray in the farm.
    """

    __tablename__ = "tray_type"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    size = Column(Float, nullable=True)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    amount_per_bench = Column(Integer, nullable=True)
    __table_args__ = {"schema": "growapp"}


class CropClass(BASE):
    """
    Details on the different types of crop.
    """

    __tablename__ = "crop"
    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    seed_density = Column(Float, nullable=True)
    propagation_period = Column(Integer, nullable=True)
    grow_period = Column(Integer, nullable=True)
    is_pre_harvest = Column(Boolean, nullable=True)
    created = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class FarmClass(BASE):
    """
    A list of farm locations.
    """

    __tablename__ = "farm"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class ZoneClass(BASE):
    """
    A list of farm zones.
    """

    __tablename__ = "zone"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farm.id"), nullable=False)
    name = Column(String(255), nullable=True)
    default_tray_type_id = Column(
        UUID(as_uuid=True), ForeignKey("tray_type.id"), nullable=False
    )
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class AisleClass(BASE):
    """
    A list of all the aisles in the farm.
    """

    __tablename__ = "aisle"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    side = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class StackClass(BASE):
    """
    A list of all the stacks/columns in the farm.
    """

    __tablename__ = "stack"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class ShelfClass(BASE):
    """
    A list of all the shelves in the farm.
    """

    __tablename__ = "shelf"

    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    name = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class LocationClass(BASE):
    """
    All possible locations in the farm.
    """

    __tablename__ = "location"
    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    zone_id = Column(
        UUID(as_uuid=True),
        ForeignKey("zone.id"),
        nullable=False,
    )
    aisle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("aisle.id"),
        nullable=False,
    )
    stack_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stack.id"),
        nullable=False,
    )
    shelf_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop.id"),
        nullable=False,
    )
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class BenchClass(BASE):
    """
    A bench at a specific location.
    """

    __tablename__ = "bench"
    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("location.id"),
        nullable=False,
    )
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}


class BatchEventClass(BASE):
    """
    Everything that happens to any batch
    """

    __tablename__ = "batch_event"
    id = Column(UUID(as_uuid=True), primary_key=True)
    type_ = Column("type", Integer, nullable=True)
    batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch.id"),
        nullable=False,
    )
    was_manual = Column(Boolean, nullable=True)
    event_happened = Column(DateTime, nullable=True)
    description = Column(String(255), nullable=True)
    next_action_days = Column(Integer, nullable=True)
    next_action = Column(DateTime, nullable=True)
    __table_args__ = {"schema": "growapp"}


class BatchClass(BASE):
    """
    Every batch that is, or has been, in the farm.
    """

    __tablename__ = "batch"
    id = Column(UUID(as_uuid=True), primary_key=True)
    version = Column(Integer, nullable=True)
    tray_size = Column(Float, nullable=True)
    number_of_trays = Column(Integer, nullable=False)
    crop_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop.id"),
        nullable=False,
    )
    tray_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tray_type.id"),
        nullable=False,
    )
    status = Column(Integer, nullable=True)
    status_date = Column(DateTime, nullable=True)
    weigh_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_event.id"),
        nullable=False,
    )
    propagation_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_event.id"),
        nullable=False,
    )
    transferred_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_event.id"),
        nullable=False,
    )
    harvested_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_event.id"),
        nullable=False,
    )
    current_bench_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bench.id"),
        nullable=False,
    )
    yield_ = Column("yield", Float, nullable=True)
    waste_disease = Column(Float, nullable=True)
    waste_defect = Column(Float, nullable=True)
    overproduction = Column(Float, nullable=True)
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    deleted = Column(Boolean, nullable=True)
    __table_args__ = {"schema": "growapp"}
