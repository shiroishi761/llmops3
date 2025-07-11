"""依存関係の互換性テスト"""
import pytest
import importlib
import sys
from packaging import version


class TestRequirementsCompatibility:
    """依存関係の互換性テスト"""
    
    def test_httpx_version_compatibility(self):
        """httpxのバージョン互換性テスト"""
        import httpx
        
        # httpxが正常にインポートできることを確認
        assert hasattr(httpx, 'Client')
        assert hasattr(httpx, 'AsyncClient')
        
        # 主要な機能が利用可能であることを確認
        client = httpx.Client()
        assert hasattr(client, 'post')
        assert hasattr(client, 'get')
        client.close()
    
    def test_langfuse_httpx_compatibility(self):
        """Langfuseとhttpxの互換性テスト"""
        try:
            import langfuse
            import httpx
            
            # Langfuseが正常にインポートできることを確認
            assert hasattr(langfuse, 'Langfuse')
            
            # httpxのバージョンがLangfuseの要求を満たしていることを確認
            httpx_version = version.parse(httpx.__version__)
            assert httpx_version >= version.parse("0.15.4")
            assert httpx_version < version.parse("1.0.0")
            
        except ImportError:
            pytest.skip("langfuse not installed")
    
    def test_google_genai_httpx_compatibility(self):
        """Google GenAIとhttpxの互換性テスト"""
        try:
            import google.genai
            import httpx
            
            # Google GenAIが正常にインポートできることを確認
            assert hasattr(google.genai, 'Client')
            
            # httpxのバージョンがGoogle GenAIの要求を満たしていることを確認
            httpx_version = version.parse(httpx.__version__)
            assert httpx_version >= version.parse("0.28.1")
            assert httpx_version < version.parse("1.0.0")
            
        except ImportError:
            pytest.skip("google-genai not installed")
    
    def test_all_required_packages_importable(self):
        """すべての必須パッケージがインポート可能であることを確認"""
        required_packages = [
            'fastapi',
            'uvicorn',
            'pydantic',
            'python_dotenv',
            'yaml',
            'httpx',
            'json5',
            'jinja2',
            'pytest'
        ]
        
        failed_imports = []
        
        for package in required_packages:
            try:
                # パッケージ名の調整
                import_name = package
                if package == 'python_dotenv':
                    import_name = 'dotenv'
                elif package == 'yaml':
                    import_name = 'yaml'
                
                importlib.import_module(import_name)
            except ImportError as e:
                failed_imports.append(f"{package}: {str(e)}")
        
        if failed_imports:
            pytest.fail(f"Failed to import packages: {failed_imports}")
    
    def test_fastapi_uvicorn_compatibility(self):
        """FastAPIとUvicornの互換性テスト"""
        import fastapi
        import uvicorn
        
        # FastAPIアプリケーションが正常に作成できることを確認
        app = fastapi.FastAPI()
        
        @app.get("/test")
        def test_endpoint():
            return {"status": "ok"}
        
        # Uvicornがアプリケーションを認識できることを確認
        assert hasattr(uvicorn, 'run')
        assert callable(uvicorn.run)
    
    def test_pydantic_version_compatibility(self):
        """Pydanticのバージョン互換性テスト"""
        import pydantic
        from pydantic import BaseModel
        
        # Pydantic v2の機能が使用可能であることを確認
        class TestModel(BaseModel):
            name: str
            value: int
        
        # モデルが正常に動作することを確認
        instance = TestModel(name="test", value=42)
        assert instance.name == "test"
        assert instance.value == 42
        
        # JSON化が正常に動作することを確認
        json_data = instance.model_dump()
        assert json_data == {"name": "test", "value": 42}