from fastapi import FastAPI
from api.v2_router.cm_router import router as cm_v2_router
from api.v2_router.auth_router import router as auth_v2_router
from api.v2_router.user_router import router as user_v2_router

from api.v1_router.cm_router import router as cm_v1_router
from api.v1_router.auth_router import router as auth_v1_router
from api.v1_router.user_router import router as user_v1_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.openapi.docs import get_swagger_ui_html

from database import init_db


def create_app() :
    """Create and configure the FastAPI application with versioned routers."""
    
    v1_app = FastAPI(title="Content Moderation API V1",
                  description="API for content moderation V1 with user authentication and two-factor authentication support.",
                  version="1.0.0"
                )
    v1_app.include_router(auth_v1_router)
    v1_app.include_router(user_v1_router)
    v1_app.include_router(cm_v1_router)
    

    v2_app = FastAPI(title="Content Moderation API V2",
                  description="API for content moderation V2 with user authentication and two-factor authentication support.",
                  version="2.0.0")
    v2_app.state.limiter = Limiter(key_func=get_remote_address)
    v2_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    v2_app.include_router(auth_v2_router)
    v2_app.include_router(user_v2_router)
    v2_app.include_router(cm_v2_router)
    

    main_app = FastAPI(title="Content Moderation API",
                  description="API for content moderation with user authentication and two-factor authentication support.",
                  docs_url="/docs",
                  redoc_url=None,
                  openapi_url=f"",
                  swagger_ui_parameters={
            "urls": [
                {
                    "url": f"/api/v1{v1_app.openapi_url}",
                    "name": "Content Moderation API V1",
                },
                {
                    "url": f"/api/v2{v2_app.openapi_url}",
                    "name": "Content Moderation API V2",
                },
            ],
            "urls.primaryName": "Content Moderation API",
            "servers": [{"url": "/api/latest" },{"url": "/api/v1"},{"url": "/api/v2"}]
        }
    )

    main_app.mount("/api/v1",v1_app)
    main_app.mount("/api/v2",v2_app)
    main_app.mount("/api/latest",v2_app)

    return main_app

if __name__ == "__main__":
    import uvicorn
    init_db()
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)