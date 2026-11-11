from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_profile
from app.database.connection import get_db
from app.models.user_model import UserProfile
from app.schemas.address_schema import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
)
from app.schemas.user_schema import MessageResponse
from app.services.address_service import AddressService

router = APIRouter(prefix="/addresses", tags=["User Addresses"])


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new delivery address",
    description="Adds a new delivery address for the authenticated user. Automatically assigns default if first address.",
)
def add_address(
    payload: AddressCreate,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Add a new address for current user."""
    address = AddressService.create_address(db=db, profile=profile, req=payload)
    return AddressResponse.model_validate(address)


@router.get(
    "",
    response_model=List[AddressResponse],
    status_code=status.HTTP_200_OK,
    summary="List current user's addresses",
    description="Retrieves all delivery addresses for the authenticated user with the default address first.",
)
def list_my_addresses(
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """List all addresses of current user."""
    addresses = AddressService.list_addresses(db=db, profile=profile)
    return [AddressResponse.model_validate(a) for a in addresses]


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific address",
    description="Retrieves details of a specific address. Enforces user ownership.",
)
def get_address_by_id(
    address_id: int,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Get single address by ID."""
    address = AddressService.get_address(db=db, profile=profile, address_id=address_id)
    return AddressResponse.model_validate(address)


@router.put(
    "/{address_id}",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an address",
    description="Updates all fields of an existing address owned by the authenticated user.",
)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Update address by ID."""
    updated = AddressService.update_address(
        db=db, profile=profile, address_id=address_id, req=payload
    )
    return AddressResponse.model_validate(updated)


@router.delete(
    "/{address_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an address",
    description="Deletes an address belonging to the authenticated user.",
)
def delete_address(
    address_id: int,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Delete address by ID."""
    AddressService.delete_address(db=db, profile=profile, address_id=address_id)
    return MessageResponse(message="Address deleted successfully.")


@router.patch(
    "/{address_id}/default",
    response_model=AddressResponse,
    status_code=status.HTTP_200_OK,
    summary="Set default address",
    description="Marks the specified address as the default delivery address and unsets all other defaults.",
)
def set_default_address(
    address_id: int,
    profile: UserProfile = Depends(get_current_user_profile),
    db: Session = Depends(get_db),
):
    """Set address as primary default."""
    address = AddressService.set_default_address(
        db=db, profile=profile, address_id=address_id
    )
    return AddressResponse.model_validate(address)

