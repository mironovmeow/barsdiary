"""
Api module (on aiohttp)
"""
from typing import Optional, Type

from loguru import logger

from . import __version__, types

try:
    from aiohttp import (
        ClientResponse,
        ClientSession,
        ClientTimeout,
        ContentTypeError,
        TCPConnector,
    )
except ImportError:
    raise ImportError(
        "'aiohttp' is not installed.\n"
        "You can fix this by running ``pip install barsdiary[async]``"
    )

USER_AGENT = f"barsdiary/{__version__}"


class APIError(types.APIError):
    def __init__(self, resp: ClientResponse, session: ClientSession, json: Optional[dict] = None):
        self.resp = resp
        self.session = session
        self.json = json

    @property
    def code(self) -> int:
        if self.json:
            return self.json.get("error_code", self.resp.status)
        else:
            return self.resp.status

    def __str__(self):
        return f"APIError [{self.resp.status}] {self.json}"

    @property
    def json_success(self) -> bool:
        if self.json:
            return self.json.get("success", False)
        return False


async def _check_response(r: ClientResponse, session: ClientSession) -> dict:
    if not r.ok:
        logger.info(f"Request failed. Bad status: {r.status}")
        raise APIError(r, session)

    try:
        json = await r.json()
        logger.debug(f"Response with {json}")

        if json.get("error") is not None:  # {"error": "Произошла непредвиденная ошибка ..."}
            json["success"] = False
            json["kind"] = json["error"]

        if json.get("success", False) is False:
            logger.info("Request failed. Not success.")
            raise APIError(r, session, json=json)

        return json

    except ContentTypeError:
        logger.info("Request failed. ContentTypeError")
        raise APIError(r, session)


class DiaryApi:
    def __init__(self, host: str, session: ClientSession, sessionid: str, user_information: dict):
        self._host = host
        self._session = session
        self.sessionid = sessionid
        self.user_information = user_information
        self.user = types.LoginObject.reformat(user_information)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()
        await self.close_session()

    def __repr__(self) -> str:
        return f"<DiaryApi {self.user.id}>"

    @property
    def closed(self) -> bool:
        return self._session.closed

    async def close_session(self) -> None:
        logger.info(f"Closing DiaryApi {self.user.fio}")
        await self._session.close()

    async def _post(
        self, cls: Type[types.ObjectType], endpoint: str, data: Optional[dict] = None
    ) -> types.ObjectType:
        logger.debug(f'Request "{endpoint}" with data {data}')
        async with self._session.post(f"https://{self._host}/rest/{endpoint}", data=data) as r:
            json = await _check_response(r, self._session)
            return cls.reformat(json)

    @classmethod
    async def auth_by_diary_session(
        cls, host: str, diary_session: str, diary_information: dict
    ) -> "DiaryApi":
        session = ClientSession(
            connector=TCPConnector(verify_ssl=False),
            headers={"User-Agent": USER_AGENT},
            cookies={"sessionid": diary_session},
            timeout=ClientTimeout(10),
        )
        return cls(host, session, diary_session, diary_information)

    @classmethod
    async def auth_by_login(cls, host: str, login: str, password: str) -> "DiaryApi":
        logger.debug('Request "login" with data {"login": ..., "password": ...}')
        session = ClientSession(
            connector=TCPConnector(verify_ssl=False),
            headers={"User-Agent": USER_AGENT},
            timeout=ClientTimeout(10),
        )
        async with session.get(
            f"https://{host}/rest/login?login={login}&password={password}"
        ) as r:
            json = await _check_response(r, session)
            diary_cookie = r.cookies.get("sessionid")
            if not diary_cookie:
                raise ValueError("Authorization failed. No cookie.")

            return cls(host, session, diary_cookie.value, json)

    async def diary(
        self, from_date: str, to_date: Optional[str] = None, *, child: int = 0
    ) -> types.DiaryObject:
        if to_date is None:
            to_date = from_date

        return await self._post(
            types.DiaryObject,
            "diary",
            {
                "pupil_id": self.user.children[child].id,
                "from_date": from_date,
                "to_date": to_date,
            },
        )

    async def progress_average(self, date: str, *, child: int = 0) -> types.ProgressAverageObject:
        return await self._post(
            types.ProgressAverageObject,
            "progress_average",
            {"pupil_id": self.user.children[child].id, "date": date},
        )

    async def additional_materials(
        self, lesson_id: int, *, child: int = 0
    ) -> types.AdditionalMaterialsObject:
        return await self._post(
            types.AdditionalMaterialsObject,
            "additional_materials",
            {"pupil_id": self.user.children[child].id, "lesson_id": lesson_id},
        )

    async def school_meetings(self, *, child: int = 0) -> types.SchoolMeetingsObject:
        return await self._post(
            types.SchoolMeetingsObject,
            "school_meetings",
            {"pupil_id": self.user.children[child].id},
        )

    async def totals(self, date: str, *, child: int = 0) -> types.TotalsObject:
        return await self._post(
            types.TotalsObject,
            "totals",
            {"pupil_id": self.user.children[child].id, "date": date},
        )

    async def lessons_scores(
        self, date: str, subject: Optional[str] = None, *, child: int = 0
    ) -> types.LessonsScoreObject:
        if subject is None:
            subject = ""

        return await self._post(
            types.LessonsScoreObject,
            "lessons_scores",
            {
                "pupil_id": self.user.children[child].id,
                "date": date,
                "subject": subject,
            },
        )

    async def logout(self) -> types.BaseResponse:
        return await self._post(types.BaseResponse, "logout")

    async def check_food(self) -> types.CheckFoodObject:
        logger.debug('Request "check_food" with data None')
        async with self._session.post(f"https://{self._host}/rest/check_food") as r:
            json = await _check_response(r, self._session)
            return types.CheckFoodObject.parse_obj(json)


__all__ = (
    "DiaryApi",
    "APIError",
)
