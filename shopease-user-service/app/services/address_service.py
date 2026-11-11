from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.address_model import UserAddress
from app.models.user_model import UserProfile
from app.schemas.address_schema import AddressCreate, AddressUpdate


class AddressService:
    """Service class handling delivery address business logic and isolation."""

    @staticmethod
    def create_address(
        db: Session,
        profile: UserProfile,
        req: AddressCreate,
    ) -> UserAddress:
        """
        Creates a new delivery address for the authenticated user.
        If marked as default (or if it's the user's first address),
        any existing default address is automatically unset.
        """
        existing_count = (
            db.query(UserAddress)
            .filter(UserAddress.user_id == profile.id)
            .count()
        )

        should_be_default = req.is_default or (existing_count == 0)

        if should_be_default:
            # Unset is_default on any existing addresses of this user
            db.query(UserAddress).filter(UserAddress.user_id == profile.id).update(
                {"is_default": False}
            )

        new_address = UserAddress(
            user_id=profile.id,
            address_type=req.address_type,
            full_name=req.full_name,
            phone_number=req.phone_number,
            address_line_1=req.address_line_1,
            address_line_2=req.address_line_2,
            city=req.city,
            state=req.state,
            country=req.country,
            postal_code=req.postal_code,
            is_default=should_be_default,
        )

        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        return new_address

    @staticmethod
    def list_addresses(
        db: Session,
        profile: UserProfile,
    ) -> List[UserAddress]:
        """
        Lists all delivery addresses belonging to the authenticated user.
        Default address appears first.
        """
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == profile.id)
            .order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
            .all()
        )

    @staticmethod
    def get_address(
        db: Session,
        profile: UserProfile,
        address_id: int,
    ) -> UserAddress:
        """
        Retrieves a specific address ensuring the authenticated user owns it.
        Returns 404 if not found, 403 if address belongs to another user.
        """
        address = (
            db.query(UserAddress)
            .filter(UserAddress.id == address_id)
            .first()
        )

        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {address_id} not found.",
            )

        # Enforce strict user-level ownership isolation
        if address.user_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view or manage this address.",
            )

        return address

    @staticmethod
    def update_address(
        db: Session,
        profile: UserProfile,
        address_id: int,
        req: AddressUpdate,
    ) -> UserAddress:
        """
        Updates an existing delivery address belonging to the user.
        Handles default address reassignment.
        """
        address = AddressService.get_address(db, profile, address_id)

        if req.is_default and not address.is_default:
            # Unset default from other addresses
            db.query(UserAddress).filter(UserAddress.user_id == profile.id).update(
                {"is_default": False}
            )

        address.address_type = req.address_type
        address.full_name = req.full_name
        address.phone_number = req.phone_number
        address.address_line_1 = req.address_line_1
        address.address_line_2 = req.address_line_2
        address.city = req.city
        address.state = req.state
        address.country = req.country
        address.postal_code = req.postal_code
        address.is_default = req.is_default

        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def delete_address(
        db: Session,
        profile: UserProfile,
        address_id: int,
    ) -> None:
        """
        Deletes a user's delivery address.
        """
        address = AddressService.get_address(db, profile, address_id)
        was_default = address.is_default

        db.delete(address)
        db.commit()

        # If the deleted address was default, promote the latest remaining address to default
        if was_default:
            remaining = (
                db.query(UserAddress)
                .filter(UserAddress.user_id == profile.id)
                .order_by(UserAddress.created_at.desc())
                .first()
            )
            if remaining:
                remaining.is_default = True
                db.commit()

    @staticmethod
    def set_default_address(
        db: Session,
        profile: UserProfile,
        address_id: int,
    ) -> UserAddress:
        """
        Sets a specific address as the default delivery address.
        Removes default status from all other addresses of this user.
        """
        address = AddressService.get_address(db, profile, address_id)

        # Unset all other addresses for this user
        db.query(UserAddress).filter(UserAddress.user_id == profile.id).update(
            {"is_default": False}
        )

        address.is_default = True
        db.commit()
        db.refresh(address)
        return address

