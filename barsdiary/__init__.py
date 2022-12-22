"""
BarsDiary Module

>>> from barsdiary.sync import DiaryApi
>>> # or barsdiary.aio
>>>
>>> with DiaryApi.auth_by_login("login", "password") as user_api:
>>>     diary = user_api.diary("12.12.2021")
>>>     lesson = diary.days[0].lessons[0]
>>>     print(lesson.discipline)
"""
from .types import (
    AdditionalMaterialsObject,
    APIError,
    CheckFoodObject,
    DiaryObject,
    LessonsScoreObject,
    LoginObject,
    ProgressAverageObject,
    SchoolMeetingsObject,
    TotalsObject,
)

# using in user-agent in requests
__version__ = "0.1.3"
