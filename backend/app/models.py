"""API入出力用のPydanticスキーマ。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.calculations.stats import MAX_EV_PER_STAT, MAX_EV_TOTAL

Item = Literal[
    "none",
    "choice-band",
    "choice-specs",
    "choice-scarf",
    "life-orb",
    "expert-belt",
    "assault-vest",
    "eviolite",
]
Weather = Literal["none", "sun", "rain", "sand", "snow"]
DamageClass = Literal["physical", "special"]


class EVs(BaseModel):
    """努力値(0〜32段階での割り振り。性格補正は段階の上がり方に織り込み済み)。"""

    hp: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)
    attack: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)
    defense: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)
    special_attack: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)
    special_defense: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)
    speed: int = Field(default=0, ge=0, le=MAX_EV_PER_STAT)

    @model_validator(mode="after")
    def check_total(self) -> "EVs":
        total = self.hp + self.attack + self.defense + self.special_attack + self.special_defense + self.speed
        if total > MAX_EV_TOTAL:
            raise ValueError(f"努力値の合計は{MAX_EV_TOTAL}以下にしてください(現在: {total})")
        return self


class IVs(BaseModel):
    hp: int = Field(default=31, ge=0, le=31)
    attack: int = Field(default=31, ge=0, le=31)
    defense: int = Field(default=31, ge=0, le=31)
    special_attack: int = Field(default=31, ge=0, le=31)
    special_defense: int = Field(default=31, ge=0, le=31)
    speed: int = Field(default=31, ge=0, le=31)


class MoveIn(BaseModel):
    slot: int = Field(ge=1, le=4)
    move_id: int
    move_name: str


class PartyMemberIn(BaseModel):
    position: int = Field(ge=1, le=6)
    species_id: int
    species_name: str
    nickname: str | None = None
    item: str | None = None
    ability: str | None = None
    nature: str
    evs: EVs = Field(default_factory=EVs)
    ivs: IVs = Field(default_factory=IVs)
    moves: list[MoveIn] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def check_unique_move_slots(self) -> "PartyMemberIn":
        slots = [m.slot for m in self.moves]
        if len(slots) != len(set(slots)):
            raise ValueError("技のスロットが重複しています")
        return self


class PartyMemberOut(PartyMemberIn):
    id: int


class PartyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    members: list[PartyMemberIn] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def check_unique_positions(self) -> "PartyIn":
        positions = [m.position for m in self.members]
        if len(positions) != len(set(positions)):
            raise ValueError("パーティ内のポジションが重複しています")
        return self


class PartyOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    members: list[PartyMemberOut]

    model_config = {"from_attributes": True}


class StatCalcRequest(BaseModel):
    base_stats: dict[str, int]
    ivs: IVs = Field(default_factory=IVs)
    evs: EVs = Field(default_factory=EVs)
    nature: str
    level: int = Field(default=50, ge=1, le=100)


class DamageSide(BaseModel):
    base_stats: dict[str, int]
    types: list[str]
    ivs: IVs = Field(default_factory=IVs)
    evs: EVs = Field(default_factory=EVs)
    nature: str
    level: int = Field(default=50, ge=1, le=100)
    item: Item = "none"


class DamageCalcRequest(BaseModel):
    attacker: DamageSide
    defender: DamageSide
    move_power: int = Field(ge=0, le=250)
    move_type: str
    move_damage_class: DamageClass
    weather: Weather = "none"
    trick_room: bool = False
    critical: bool = False
