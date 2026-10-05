from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import (
    ModelStatus,
    ModelType,
    SignalModel,
)


def get_models(
    db: Session,
) -> list[SignalModel]:

    statement = (
        select(SignalModel)
        .order_by(
            SignalModel.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_model(
    db: Session,
    model_id: uuid.UUID,
) -> SignalModel | None:

    statement = select(
        SignalModel
    ).where(
        SignalModel.id == model_id
    )

    return db.scalar(statement)


def create_model(
    db: Session,
    *,
    name: str,
    version: str,
    model_type: str,
    description: str | None,
    board_size: int,
    maximum_attempts: int,
    confidence_score: float | None,
) -> SignalModel:

    try:
        parsed_model_type = ModelType(
            model_type.upper()
        )
    except ValueError:
        raise ValueError(
            "Invalid model type. "
            "Use PRODUCTION, EXPERIMENTAL, "
            "or DEVELOPMENT."
        )

    existing_version = db.scalar(
        select(SignalModel).where(
            SignalModel.version == version.strip()
        )
    )

    if existing_version is not None:
        raise ValueError(
            "A model with this version already exists."
        )

    model = SignalModel(
        id=uuid.uuid4(),
        version=version.strip(),
        name=name.strip(),
        model_type=parsed_model_type,
        status=ModelStatus.READY,
        description=description,
        board_size=board_size,
        maximum_attempts=maximum_attempts,
        confidence_score=confidence_score,
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model


def update_model(
    db: Session,
    model: SignalModel,
    values: dict,
) -> SignalModel:

    if "model_type" in values:
        try:
            values["model_type"] = ModelType(
                values["model_type"].upper()
            )
        except ValueError:
            raise ValueError(
                "Invalid model type. "
                "Use PRODUCTION, EXPERIMENTAL, "
                "or DEVELOPMENT."
            )

    if "version" in values:
        new_version = values["version"].strip()

        existing_version = db.scalar(
            select(SignalModel).where(
                SignalModel.version == new_version,
                SignalModel.id != model.id,
            )
        )

        if existing_version is not None:
            raise ValueError(
                "A model with this version already exists."
            )

        values["version"] = new_version

    if "name" in values:
        values["name"] = values["name"].strip()

    for field, value in values.items():
        setattr(
            model,
            field,
            value,
        )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model


def activate_model(
    db: Session,
    model: SignalModel,
) -> SignalModel:

    # Only one ACTIVE model is allowed
    # for a particular board size.

    statement = (
        select(SignalModel)
        .where(
            SignalModel.board_size
            == model.board_size,

            SignalModel.status
            == ModelStatus.ACTIVE,

            SignalModel.id
            != model.id,
        )
    )

    active_models = list(
        db.scalars(statement).all()
    )

    for active_model in active_models:
        active_model.status = (
            ModelStatus.ARCHIVED
        )

    model.status = ModelStatus.ACTIVE

    model.activated_at = datetime.now(
        timezone.utc
    )

    db.add(model)

    db.commit()
    db.refresh(model)

    return model


def archive_model(
    db: Session,
    model: SignalModel,
) -> SignalModel:

    if model.status == ModelStatus.ACTIVE:
        raise ValueError(
            "An active model must be replaced "
            "by activating another model before "
            "it can be archived."
        )

    model.status = ModelStatus.ARCHIVED

    db.add(model)

    db.commit()
    db.refresh(model)

    return model


def delete_model(
    db: Session,
    model: SignalModel,
) -> None:

    if model.status == ModelStatus.ACTIVE:
        raise ValueError(
            "Active models cannot be deleted. "
            "Archive or replace the model first."
        )

    db.delete(model)
    db.commit()