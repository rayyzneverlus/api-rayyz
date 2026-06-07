from fastapi.openapi.utils import get_openapi

def setup_docs(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        # Generator skema bawaan FastAPI otomatis mengumpulkan rute & tags
        openapi_schema = get_openapi(
            title="Farel Api's",
            version="1.5.2",
            description="Easy To Use",
            routes=app.routes,
        )
        
        # Ambil semua tag unik yang ada di dalam aplikasi secara dinamis
        extracted_tags = set()
        for route in app.routes:
            if hasattr(route, "tags"):
                for tag in route.tags:
                    extracted_tags.add(tag)
                    
        # Masukkan daftar tags yang terdeteksi ke dalam skema OpenAPI
        openapi_schema["tags"] = [{"name": tag} for tag in sorted(list(extracted_tags))]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
        
    app.openapi = custom_openapi
