import uuid

from fastapi import Depends, HTTPException

from controller.auth import ScopeValidator
from models import Role, RoleCreate
from models import UserRead, User
from models.user import RoleRead
from utils.models import ObjectIdentifier
from utils.router import Models, UniqueNameRouter

role_models = Models(base=Role, create=RoleCreate, read=RoleRead)


class RoleRouter(UniqueNameRouter):

    def __init__(self):
        super().__init__(role_models, tag="roles", prefix="/roles")

    def extension(self):
        router = self

        @router.post("/{user_id}/roles/{role_name}", response_model=UserRead)
        def assign_role_to_user(role_name: str, user_id: uuid.UUID,
                                _: None = Depends(ScopeValidator("roles:assign"))):
            user = router.crud.read(Role, ObjectIdentifier(id=user_id), model=User)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            role = router.crud.read_raw(Role, name___id=role_name)
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            if not role in user.roles:
                user.roles.append(role)
                router.crud.refresh(user)

            return user
