"""
BarsDiary Types (on pydantic)
"""
import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence, Type, TypeVar, Union

from pydantic import BaseModel, Field

ObjectType = TypeVar("ObjectType", bound="BaseResponse")


class APIError(ABC, BaseException):
    @abstractmethod
    def __init__(self, resp, session, json):
        ...

    @property
    @abstractmethod
    def code(self) -> int:
        ...

    @abstractmethod
    def __str__(self):
        ...

    @property
    @abstractmethod
    def json_success(self) -> bool:
        ...


class BaseResponse(BaseModel):
    success: bool  # checking in sync.py and aio.py

    @classmethod
    def reformat(cls: Type[ObjectType], obj: dict) -> ObjectType:
        return cls.parse_obj(obj)


# /rest/login


class ChildObject(BaseModel):
    id: int
    name: str
    school: str


class LoginObject(BaseResponse):
    children: List[ChildObject]
    profile_id: int
    id: int
    type: str
    fio: str

    @classmethod
    def reformat(cls: Type[ObjectType], obj: dict) -> ObjectType:
        return cls.parse_obj(
            {
                "success": obj.get("success"),
                "children": [
                    {"id": child[0], "name": child[1], "school": child[2]}
                    for child in obj.get("childs", [])  # stupid api
                ],
                "profile_id": obj.get("profile_id"),
                "id": obj.get("id"),
                "type": obj.get("type"),
                "fio": obj.get("fio"),
            }
        )


# /rest/diary


class DiaryLessonObject(BaseModel):  # TODO
    comment: str
    discipline: str
    remark: str  # what it?  now it's ''
    attendance: Union[list, str]  # what it?  now it's ['', 'Был']
    room: str
    next_homework: Sequence[Union[str, None]]  # first: str or none, second: ''
    individual_homework: list = Field(
        alias="individualhomework"
    )  # for beautiful use in code, now it []
    marks: List[list]  # [list for marks name, list of marks]  API IS SO STUPID!!!
    date_str: str = Field(alias="date")  # 21.12.2012
    lesson: list  # [id, str, start_time_str, end_time_str]
    homework: List[str]
    teacher: str
    next_individual_homework: list = Field(alias="next_individualhomework")  # check structure
    subject: str

    @property
    def date(self) -> datetime.date:
        return datetime.date(*map(int, self.date_str.split(".")[::-1]))  # do it better?


class DiaryDayObject(BaseModel):
    kind: Optional[str]
    date_str: str = Field(alias="date")  # 21.12.2012
    lessons: Optional[List[DiaryLessonObject]]

    @property
    def date(self) -> datetime.date:
        return datetime.date(*map(int, self.date_str.split(".")[::-1]))


class DiaryObject(BaseResponse):
    days: List[DiaryDayObject]

    @classmethod
    def reformat(cls: Type[ObjectType], obj: dict) -> ObjectType:
        data = {"success": obj.get("success", False), "days": []}
        for value_day in obj.get("days", []):
            day = {
                "date": value_day[0],
                "lessons": value_day[1].get("lessons"),
                "kind": value_day[1].get("kind"),
            }
            data["days"].append(day)
        return cls.parse_obj(data)


# /rest/progress_average


class ProgressDataObject(BaseModel):
    total: Optional[float]
    data: Optional[Dict[str, float]]  # discipline: mark


class ProgressAverageObject(BaseResponse):
    kind: Optional[str]
    self: ProgressDataObject
    class_year: ProgressDataObject = Field(alias="classyear")
    level: ProgressDataObject
    sub_period: str = Field(alias="subperiod")


# /rest/additional_materials


class AdditionalMaterialsObject(BaseResponse):
    kind: Optional[str]  # 26.04.2021  todo


# /rest/school_meetings


class SchoolMeetingsObject(BaseResponse):
    kind: Optional[str]


# /rest/totals


class TotalsObject(BaseResponse):  # todo how to do it better
    period: str
    period_types: List[str]  # ['1 Полугодие', '2 Полугодие', 'Годовая']
    subjects: Dict[str, List[str]]  # 'Русский язык': ['4', '0', '0']
    period_begin: str
    period_end: str


# /lessons_scores


class ScoreObject(BaseModel):
    date: str  # 2012-21-12
    marks: Dict[str, List[str]]  # text: [marks (str)]


class LessonsScoreObject(BaseResponse):
    kind: Optional[str]
    sub_period: Optional[str] = Field(alias="subperiod")
    data: Optional[Dict[str, List[ScoreObject]]]  # lesson: ScoreObject


# /check_food


class CheckFoodObject(BaseModel):
    food_plugin: str  # "NO" and maybe "YES"


__all__ = (
    "APIError",
    "BaseResponse",
    "ChildObject",
    "LoginObject",
    "DiaryLessonObject",
    "DiaryDayObject",
    "DiaryObject",
    "ProgressDataObject",
    "ProgressAverageObject",
    "AdditionalMaterialsObject",
    "SchoolMeetingsObject",
    "TotalsObject",
    "ScoreObject",
    "LessonsScoreObject",
    "CheckFoodObject",
)
