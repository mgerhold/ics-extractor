from pathlib import Path

from pydantic import BaseModel
from typing import Final, Self, final


@final
class Config(BaseModel):
    therapy_practice_address: list[str] = [
        "Therapiezentrum am Stadtpark",
        "Stadtpark 1",
        "12345 Musterstadt",
    ]
    therapy_kind_mapping: dict[str, str] = {
        "KG ZNS": "Krankengymnastik",
        "O60": "Osteopathie",
    }
    appointment_duration_minutes: int = 30
    
    @classmethod
    def load_or_default(cls, path: Path) -> Self:
        if path.exists():
            contents: Final = path.read_text(encoding="utf-8")
            return cls.model_validate_json(contents)
        else:
            config: Final = cls()
            path.write_text(
                config.model_dump_json(indent=4),
                encoding="utf-8",
            )
            return config
