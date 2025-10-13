import csv
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional


# ---------- ENUMS ----------
class PaxType(str, Enum):
    ADULT = "ADT"
    CHILD = "CHD"
    INFANT = "INF"


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"


class Preference(str, Enum):
    SOLO = "solo"
    TWIN = "twin"
    ANY = "any"


class RoomType(str, Enum):
    SINGLE = "Single"
    TWIN = "Twin"
    TRIPLE = "Triple"


# ---------- MODEL ----------
@dataclass(slots=True)
class Passenger:
    pax_id: str
    name: str
    pnr: str
    pax_type: PaxType
    age: int
    gender: Gender
    arrival_time: datetime
    family_id: Optional[str] = None
    language: Optional[str] = None
    preference: Optional[Preference] = None
    special_needs: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    booking_party_id: Optional[str] = None
    lead: bool = False
    proposed_room_type: Optional[RoomType] = None
    proposed_partner_names: Optional[str] = None


# ---------- LOADERS ----------
def load_rules(path: str = "rules.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_passengers(csv_path: str) -> List[Passenger]:
    passengers = []
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            passengers.append(Passenger(
                pax_id=row["PaxID"],
                name=row["Name"],
                pnr=row["PNR"],
                pax_type=PaxType(row["PaxType"]),
                age=int(row["Age"]),
                gender=Gender(row["Gender"]),
                arrival_time=datetime.fromisoformat(row["ArrivalTime"]),
                family_id=row["FamilyID"] or None,
                language=row["Language"] or None,
                preference=Preference(
                    row["Preference"]) if row["Preference"] else None,
                special_needs=row["SpecialNeeds"] if row["SpecialNeeds"] not in [
                    "", "None"] else None,
                phone=row["Phone"] or None,
                email=row["Email"] or None,
            ))
    return passengers


# ---------- SCORING ----------
def compute_score(p1: Passenger, p2: Passenger, rules: dict) -> int:
    if p1.pax_id == p2.pax_id:
        return rules.get("solo_base", 0)

    score = 0

    if p1.gender == p2.gender:
        score += rules.get("gender_match", 0)

    if abs(p1.arrival_time - p2.arrival_time) <= timedelta(hours=3):
        score += rules.get("arrival_close", 0)

    if p1.preference == Preference.SOLO or p2.preference == Preference.SOLO:
        score += rules.get("preference_conflict", 0)
    elif p1.preference == p2.preference:
        score += rules.get("preference_match", 0)

    if p1.family_id and p1.family_id == p2.family_id:
        score += rules.get("same_family", 0)
    else:
        score += rules.get("different_family", 0)

    if p1.language and p1.language == p2.language:
        score += rules.get("language_match", 0)

    return score


# ---------- ASSIGNMENT ----------
def assign_rooms(passengers: List[Passenger], rules: dict):
    pairs = []
    n = len(passengers)
    for i in range(n):
        for j in range(i, n):
            score = compute_score(passengers[i], passengers[j], rules)
            pairs.append((i, j, score))

    pairs.sort(key=lambda x: x[2], reverse=True)
    assigned = set()
    results = []

    for i, j, score in pairs:
        if i in assigned or j in assigned:
            continue

        p1 = passengers[i]
        p2 = passengers[j] if i != j else None
        room_id = str(uuid.uuid4())[:8]

        p1.booking_party_id = room_id
        p1.lead = True

        if p2:
            p2.booking_party_id = room_id
            p1.proposed_room_type = p2.proposed_room_type = RoomType.TWIN
            p1.proposed_partner_names = p2.name
            p2.proposed_partner_names = p1.name
        else:
            p1.proposed_room_type = RoomType.SINGLE
            p1.proposed_partner_names = None

        results.append((p1, p2 if p2 else None, score))
        assigned.add(i)
        if p2:
            assigned.add(j)

    return results


def format_results_json(results) -> List[dict]:
    """Format results as JSON"""
    output = []
    booking_party_counter = 1

    for p1, p2, score in results:
        members_info = [{
            'PaxID': p1.pax_id,
            'Name': p1.name,
            'Age': p1.age,
            'Gender': p1.gender.value,
            'PaxType': p1.pax_type.value,
            'Language': p1.language,
            'Phone': p1.phone,
            'Email': p1.email,
            'SpecialNeeds': p1.special_needs,
            'FamilyID': p1.family_id,
            'Preference': p1.preference.value if p1.preference else None
        }]

        if p2:
            members_info.append({
                'PaxID': p2.pax_id,
                'Name': p2.name,
                'Age': p2.age,
                'Gender': p2.gender.value,
                'PaxType': p2.pax_type.value,
                'Language': p2.language,
                'Phone': p2.phone,
                'Email': p2.email,
                'SpecialNeeds': p2.special_needs,
                'FamilyID': p2.family_id,
                'Preference': p2.preference.value if p2.preference else None
            })

        assignment = {
            "BookingPartyID": f"BP{booking_party_counter:03d}",
            "RoomType": "Twin" if p2 else "Single",
            "LeadPaxID": p1.pax_id,
            "LeadPaxName": p1.name,
            "Members": [p1.pax_id] + ([p2.pax_id] if p2 else []),
            "MembersDetails": members_info,
            "GuestsCount": 2 if p2 else 1,
            "Score": score
        }
        output.append(assignment)
        booking_party_counter += 1

    return output
