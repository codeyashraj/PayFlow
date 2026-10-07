from fastapi import APIRouter,HTTPException,Query
from app.api.dependencies import CurrentUser,DBSession
from app.core.exceptions import InvalidOrderStateError,NotFoundError
from app.schemas.order import OrderCreateRequest,OrderResponse,PaginatedOrdersResponse
from app.services.orders import OrderService
router=APIRouter(prefix="/api/v1/orders",tags=["orders"])
@router.post("",response_model=OrderResponse,status_code=201)
async def create(payload:OrderCreateRequest,current_user:CurrentUser,session:DBSession): return await OrderService(session).create_order(current_user.id,payload)
@router.get("",response_model=PaginatedOrdersResponse)
async def list_orders(current_user:CurrentUser,session:DBSession,page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100)):
    rows,p,ps,total,pages=await OrderService(session).list_orders(current_user.id,page,page_size); return {"items":rows,"page":p,"page_size":ps,"total":total,"total_pages":pages}
@router.get("/{order_id}",response_model=OrderResponse)
async def get(order_id:str,current_user:CurrentUser,session:DBSession):
    try:
        data=await OrderService(session).get_order(current_user.id,__import__('uuid').UUID(order_id))
        if isinstance(data,dict): return data
        return data
    except (NotFoundError,ValueError): raise HTTPException(404,"Order not found")
@router.post("/{order_id}/cancel",response_model=OrderResponse)
async def cancel(order_id:str,current_user:CurrentUser,session:DBSession):
    try: return await OrderService(session).cancel(current_user.id,__import__('uuid').UUID(order_id))
    except NotFoundError: raise HTTPException(404,"Order not found")
    except InvalidOrderStateError as e: raise HTTPException(409,str(e))
