"""
DiaryApi Module

>>> from barsdiary import DiaryApi
>>>
>>> user_api = await DiaryApi.auth_by_login("login", "password")
>>> async with user_api:
>>>     diary = await user_api.diary("12.12.2021")
>>>     lesson = diary.days[0].lessons[0]
>>>     print(lesson.discipline)
"""
from .api import DiaryApi
from .types import (APIError, AdditionalMaterialsObject, CheckFoodObject, DiaryObject, LessonsScoreObject, LoginObject,
                    ProgressAverageObject, SchoolMeetingsObject, TotalsObject)
