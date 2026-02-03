"""Beverage service with business logic and transformations"""

from sqlalchemy.ext.asyncio import AsyncSession

from db.beverages import Beverages as BeveragesDB
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from lib import logging
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class BeverageService:
    """Service for beverage-related operations"""

    @staticmethod
    async def transform_response(
        beverage,
        db_session: AsyncSession,
        include_batches=True,
        image_transitions=None,
        include_location=True,
        **kwargs,
    ):
        """Transform beverage model to response dict with camelCase keys"""
        if not beverage:
            return None

        data = beverage.to_dict()

        # Include batches if requested
        if include_batches:
            await beverage.awaitable_attrs.batches
            if beverage.batches:
                from services.batches import BatchService

                data["batches"] = [
                    await BatchService.transform_response(
                        b, db_session=db_session, include_location=include_location
                    )
                    for b in beverage.batches
                ]

        # Add image transitions
        if not image_transitions:
            image_transitions = await ImageTransitionsDB.query(db_session, beverage_id=beverage.id)

        if image_transitions:
            data["image_transitions"] = [transform_dict_to_camel_case(it.to_dict()) for it in image_transitions]

        return transform_dict_to_camel_case(data)

    @staticmethod
    async def process_image_transitions(db_session: AsyncSession, image_transitions_data, **kwargs):
        """Process image transitions from request"""
        if not image_transitions_data:
            return None

        ret_data = []
        for transition in image_transitions_data:
            transition_dict = transition.model_dump() if hasattr(transition, "model_dump") else transition
            transition_dict.update(kwargs)

            if transition_dict.get("id"):
                transition_id = transition_dict.pop("id")
                LOGGER.debug("Updating image transition %s with: %s", transition_id, transition_dict)
                ret_data.append(await ImageTransitionsDB.update(db_session, transition_id, **transition_dict))
            else:
                LOGGER.debug("Creating image transition with: %s", transition_dict)
                ret_data.append(await ImageTransitionsDB.create(db_session, **transition_dict))

        return ret_data
