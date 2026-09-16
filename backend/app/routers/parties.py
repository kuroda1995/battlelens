from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import EVs, IVs, MoveIn, PartyIn, PartyMemberOut, PartyOut
from app.models_orm import Party, PartyMember, PartyMemberMove

router = APIRouter(prefix="/parties", tags=["parties"])


def _build_party_member_orm(member_in) -> PartyMember:
    return PartyMember(
        position=member_in.position,
        species_id=member_in.species_id,
        species_name=member_in.species_name,
        nickname=member_in.nickname,
        item=member_in.item,
        ability=member_in.ability,
        nature=member_in.nature,
        ev_hp=member_in.evs.hp,
        ev_attack=member_in.evs.attack,
        ev_defense=member_in.evs.defense,
        ev_special_attack=member_in.evs.special_attack,
        ev_special_defense=member_in.evs.special_defense,
        ev_speed=member_in.evs.speed,
        iv_hp=member_in.ivs.hp,
        iv_attack=member_in.ivs.attack,
        iv_defense=member_in.ivs.defense,
        iv_special_attack=member_in.ivs.special_attack,
        iv_special_defense=member_in.ivs.special_defense,
        iv_speed=member_in.ivs.speed,
        moves=[
            PartyMemberMove(move_slot=m.slot, move_id=m.move_id, move_name=m.move_name)
            for m in member_in.moves
        ],
    )


def _member_to_out(member: PartyMember) -> PartyMemberOut:
    return PartyMemberOut(
        id=member.id,
        position=member.position,
        species_id=member.species_id,
        species_name=member.species_name,
        nickname=member.nickname,
        item=member.item,
        ability=member.ability,
        nature=member.nature,
        evs=EVs(
            hp=member.ev_hp,
            attack=member.ev_attack,
            defense=member.ev_defense,
            special_attack=member.ev_special_attack,
            special_defense=member.ev_special_defense,
            speed=member.ev_speed,
        ),
        ivs=IVs(
            hp=member.iv_hp,
            attack=member.iv_attack,
            defense=member.iv_defense,
            special_attack=member.iv_special_attack,
            special_defense=member.iv_special_defense,
            speed=member.iv_speed,
        ),
        moves=[
            MoveIn(slot=m.move_slot, move_id=m.move_id, move_name=m.move_name)
            for m in member.moves
        ],
    )


def _party_to_out(party: Party) -> PartyOut:
    return PartyOut(
        id=party.id,
        name=party.name,
        created_at=party.created_at,
        updated_at=party.updated_at,
        members=[_member_to_out(m) for m in party.members],
    )


def _get_party_or_404(db: Session, party_id: int) -> Party:
    party = (
        db.query(Party)
        .options(selectinload(Party.members).selectinload(PartyMember.moves))
        .filter(Party.id == party_id)
        .first()
    )
    if party is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="パーティが見つかりません")
    return party


@router.get("", response_model=list[PartyOut])
def list_parties(db: Session = Depends(get_db)) -> list[PartyOut]:
    parties = (
        db.query(Party)
        .options(selectinload(Party.members).selectinload(PartyMember.moves))
        .order_by(Party.updated_at.desc())
        .all()
    )
    return [_party_to_out(p) for p in parties]


@router.post("", response_model=PartyOut, status_code=status.HTTP_201_CREATED)
def create_party(payload: PartyIn, db: Session = Depends(get_db)) -> PartyOut:
    party = Party(name=payload.name, members=[_build_party_member_orm(m) for m in payload.members])
    db.add(party)
    db.commit()
    return _party_to_out(_get_party_or_404(db, party.id))


@router.get("/{party_id}", response_model=PartyOut)
def get_party(party_id: int, db: Session = Depends(get_db)) -> PartyOut:
    return _party_to_out(_get_party_or_404(db, party_id))


@router.put("/{party_id}", response_model=PartyOut)
def update_party(party_id: int, payload: PartyIn, db: Session = Depends(get_db)) -> PartyOut:
    party = _get_party_or_404(db, party_id)
    party.name = payload.name
    party.members = [_build_party_member_orm(m) for m in payload.members]
    db.commit()
    return _party_to_out(_get_party_or_404(db, party_id))


@router.delete("/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_party(party_id: int, db: Session = Depends(get_db)) -> None:
    party = _get_party_or_404(db, party_id)
    db.delete(party)
    db.commit()
