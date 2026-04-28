from fastapi import FastAPI

from src.routes.clients import router as clients_router
from src.routes.health import router as health_router
from src.routes.invoices import router as invoices_router
from src.routes.products import router as products_router
from src.routes.quotes import router as quotes_router

app = FastAPI(
    title="Qonto API Proxy",
    description="Per-client Railway proxy that holds Qonto credentials and forwards requests.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(quotes_router)
app.include_router(invoices_router)
app.include_router(clients_router)
app.include_router(products_router)
