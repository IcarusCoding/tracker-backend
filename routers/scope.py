from fastapi import Depends, HTTPException

from controller.auth import ScopeValidator
from models import Role
from models.user import Scope, ScopeCreate
from utils.router import Models, UniqueNameRouter

scope_models = Models(base=Scope, create=ScopeCreate, read=Scope)


class ScopeRouter(UniqueNameRouter):

    def __init__(self):
        super().__init__(scope_models, tag="scopes", prefix="/scopes")

    def extension(self):
        router = self

        @router.post("/{role_name}/scopes/{scope_name}", response_model=Role)
        def assign_scope_to_role(role_name: str, scope_name: str,
                                 _: None = Depends(ScopeValidator("scopes:assign"))):
            role = router.crud.read_raw(Role, name___is=role_name)
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")

            scope = router.crud.read_raw(Scope, name___is=scope_name)
            if not scope:
                raise HTTPException(status_code=404, detail="Scope not found")

            if not scope in role.scopes:
                role.scopes.append(role)
                router.crud.refresh(role)

            return role
