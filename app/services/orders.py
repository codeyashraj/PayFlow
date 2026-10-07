from decimal import Decimal
from math import ceil
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import InvalidOrderStateError, NotFoundError
from app.models.order import Order, OrderItem, OrderStatus
from app.repositories.orders import OrderRepository
from app.services import order_cache
class OrderService:
    def __init__(self,session:AsyncSession): self.session=session; self.repo=OrderRepository(session)
    async def create_order(self,user_id,payload):
        total=sum((i.unit_price*i.quantity for i in payload.items),Decimal("0.00")).quantize(Decimal("0.01"))
        order=Order(user_id=user_id,total_amount=total,currency=payload.currency,status=OrderStatus.PENDING)
        order.items=[OrderItem(product_name=i.product_name,quantity=i.quantity,unit_price=i.unit_price) for i in payload.items]
        self.session.add(order); await self.session.commit(); await self.session.refresh(order); return order
    async def get_order(self,user_id,order_id):
        cached=await order_cache.get(user_id,order_id)
        if cached: return cached
        order=await self.repo.get_by_id_for_user(order_id,user_id)
        if not order: raise NotFoundError("Order not found")
        data={"id":str(order.id),"status":order.status,"total_amount":str(order.total_amount),"currency":order.currency,"created_at":order.created_at.isoformat(),"updated_at":order.updated_at.isoformat() if order.updated_at else None,"items":[{"id":str(i.id),"product_name":i.product_name,"quantity":i.quantity,"unit_price":str(i.unit_price)} for i in order.items]}
        await order_cache.set(user_id,order_id,data); return data
    async def list_orders(self,user_id,page,page_size):
        rows,total=await self.repo.list_for_user(user_id,(page-1)*page_size,page_size)
        return rows,page,page_size,total,ceil(total/page_size) if total else 0
    async def cancel(self,user_id,order_id):
        order=await self.repo.get_by_id_for_user(order_id,user_id,for_update=True)
        if not order: raise NotFoundError("Order not found")
        if order.status!=OrderStatus.PENDING: raise InvalidOrderStateError("Only pending orders can be cancelled")
        order.status=OrderStatus.CANCELLED; await self.session.commit(); await self.session.refresh(order); await order_cache.invalidate(user_id,order_id); return order
