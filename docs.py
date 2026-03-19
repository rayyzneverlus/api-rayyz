from fastapi.openapi.utils import get_openapi

def setup_docs(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Farel Api's",
            version="1.5.2",
            description="Easy To Use",
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    app.openapi = custom_openapi
