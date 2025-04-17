from typing import Dict, Any
import time

class MemoryCache:
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def set(cls, key: str, value: Any, expire: int = 300):
        cls._cache[key] = {
            "value": value,
            "expire": time.time() + expire
        }
    
    @classmethod
    def get(cls, key: str) -> Any:
        if key not in cls._cache:
            return None
            
        cache_data = cls._cache[key]
        if time.time() > cache_data["expire"]:
            del cls._cache[key]
            return None
            
        return cache_data["value"]
    
    @classmethod
    def delete(cls, key: str):
        if key in cls._cache:
            del cls._cache[key] 