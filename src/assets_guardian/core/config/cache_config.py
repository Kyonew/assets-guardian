from dataclasses import dataclass
from typing import Any

from assets_guardian.core.config.loader import get_config_value
from assets_guardian.core.domain.models.validator import validate_field

DEFAULT_CACHE_BATCH_SIZE = "64"
DEFAULT_CACHE_DIR = ".assets-guardian_cache"


@dataclass
class CacheConfig:
    """Cache configuration.

    Attributes:
        batch_size (int): Size of batches for cache read/write operations.
        cache_dir (str): Directory where cache is stored.
    """

    batch_size: int
    cache_dir: str

    def __post_init__(self) -> None:
        validate_field(self, "batch_size", int)
        validate_field(self, "cache_dir", str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheConfig":
        return cls(
            batch_size=int(
                get_config_value(
                    "batch_size",
                    data,
                    default=DEFAULT_CACHE_BATCH_SIZE,
                    env_name="CACHE_BATCH_SIZE",
                )
            ),
            cache_dir=get_config_value(
                "cache_dir",
                data,
                default=DEFAULT_CACHE_DIR,
                env_name="CACHE_DIR",
            ),
        )
