from app.crud.base import CRUDBase
from app.models.local import Local
from app.schemas.local import LocalCreate, LocalUpdate

local_crud = CRUDBase[Local, LocalCreate, LocalUpdate](Local)