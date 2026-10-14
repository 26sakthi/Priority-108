import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.schemas.domain import QuestionSchema, QuestionOption

QUESTION_BANK_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "QUESTION_BANK.json"

DEFAULT_ESSENTIAL_QUESTIONS = [
    {
        "question_id": "Q_EVENT_TYPE",
        "category": "ESSENTIAL",
        "text": "What type of emergency occurred?",
        "question_type": "SINGLE_CHOICE",
        "is_essential": True,
        "options": [
            {"value": "ROAD_TRAFFIC_ACCIDENT", "label": "Vehicle Accident / Collision", "urgency_weight": 30},
            {"value": "CARDIAC_CHEST_PAIN", "label": "Chest Pain / Heart Attack", "urgency_weight": 40},
            {"value": "UNCONSCIOUS_FALL", "label": "Unconscious / Severe Fall", "urgency_weight": 35},
            {"value": "RESPIRATORY", "label": "Severe Breathing Difficulty / Choking", "urgency_weight": 40},
            {"value": "STROKE_NEURO", "label": "Sudden Weakness / Slurred Speech", "urgency_weight": 35},
            {"value": "OTHER", "label": "Other Emergency", "urgency_weight": 15}
        ]
    },
    {
        "question_id": "Q_CONSCIOUSNESS",
        "category": "ESSENTIAL",
        "text": "Is the patient conscious?",
        "question_type": "SINGLE_CHOICE",
        "is_essential": True,
        "options": [
            {"value": "ALERT", "label": "Alert and talking normally", "urgency_weight": 0},
            {"value": "DROWSY", "label": "Drowsy / Responds only to voice or pain", "urgency_weight": 25},
            {"value": "UNRESPONSIVE", "label": "Completely unresponsive / unconscious", "urgency_weight": 40}
        ]
    },
    {
        "question_id": "Q_BREATHING",
        "category": "ESSENTIAL",
        "text": "Is the patient breathing normally?",
        "question_type": "SINGLE_CHOICE",
        "is_essential": True,
        "options": [
            {"value": "NORMAL", "label": "Normal, regular breathing", "urgency_weight": 0},
            {"value": "DIFFICULT", "label": "Struggling to breathe / Agonal", "urgency_weight": 35},
            {"value": "ABSENT", "label": "NOT breathing / Gasping", "urgency_weight": 100, "trigger_instant_p1": True}
        ]
    },
    {
        "question_id": "Q_BLEEDING",
        "category": "ESSENTIAL",
        "text": "Is there severe, uncontrolled bleeding?",
        "question_type": "SINGLE_CHOICE",
        "is_essential": True,
        "options": [
            {"value": "NONE", "label": "No major bleeding", "urgency_weight": 0},
            {"value": "MODERATE", "label": "Controlled bleeding", "urgency_weight": 15},
            {"value": "SEVERE_PUMPING", "label": "Severe pumping / gushing blood", "urgency_weight": 45, "trigger_instant_p1": True}
        ]
    },
    {
        "question_id": "Q_LOCATION_CONFIRM",
        "category": "ESSENTIAL",
        "text": "Confirm exact accident spot / nearby milestone or landmark:",
        "question_type": "TEXT",
        "is_essential": True,
        "options": []
    }
]

class QuestionEngine:
    def __init__(self):
        self.question_bank = self._load_question_bank()

    def _load_question_bank(self) -> Dict[str, Any]:
        if QUESTION_BANK_PATH.exists():
            try:
                with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "essential_questions": DEFAULT_ESSENTIAL_QUESTIONS,
            "adaptive_modules": {}
        }

    def get_essential_questions(self) -> List[QuestionSchema]:
        raw_list = self.question_bank.get("essential_questions", DEFAULT_ESSENTIAL_QUESTIONS)
        return [
            QuestionSchema(
                question_id=q["question_id"],
                category=q.get("category", "ESSENTIAL"),
                text=q["text"],
                question_type=q["question_type"],
                is_essential=q.get("is_essential", True),
                options=[
                    QuestionOption(
                        value=opt["value"],
                        label=opt["label"],
                        urgency_weight=opt.get("urgency_weight", 0),
                        trigger_instant_p1=opt.get("trigger_instant_p1", False)
                    )
                    for opt in q.get("options", [])
                ]
            )
            for q in raw_list
        ]

    def get_adaptive_questions(self, incident_type: str) -> List[QuestionSchema]:
        modules = self.question_bank.get("adaptive_modules", {})
        raw_list = modules.get(incident_type, [])
        return [
            QuestionSchema(
                question_id=q["question_id"],
                category=q.get("category", "ADAPTIVE"),
                text=q["text"],
                question_type=q["question_type"],
                is_essential=False,
                options=[
                    QuestionOption(
                        value=opt["value"],
                        label=opt["label"],
                        urgency_weight=opt.get("urgency_weight", 0),
                        trigger_instant_p1=opt.get("trigger_instant_p1", False)
                    )
                    for opt in q.get("options", [])
                ]
            )
            for q in raw_list
        ]

question_engine = QuestionEngine()
