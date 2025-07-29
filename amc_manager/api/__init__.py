"""API routers package"""

from .auth import router as auth_router
from .instances import router as instances_router
from .workflows import router as workflows_router
from .executions import router as executions_router
from .campaigns import router as campaigns_router
from .queries import router as queries_router

__all__ = [
    'auth_router',
    'instances_router',
    'workflows_router',
    'executions_router',
    'campaigns_router',
    'queries_router'
]