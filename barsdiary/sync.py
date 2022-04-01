"""
Api module (on httpx)
"""
from json import JSONDecodeError
from typing import Optional, Type

from loguru import logger

from . import __version__, types

try:
    from httpx import Client, Response
except ImportError:
    raise ImportError(
        "'httpx' is not installed.\nYou can fix this by running ``pip install barsdiary[sync]``"
    )

USER_AGENT = f"barsdiary/{__version__}"


class APIError(types.APIError):
    def __init__(self, resp: Response, session: Client, json: Optional[dict] = None):
        self.resp = resp
        self.session = session
        self.json = json

    @property
    def code(self) -> int:
        if self.json:
            return self.json.get("error_code", self.resp.status_code)
        else:
            return self.resp.status_code

    def __str__(self):
        return f"APIError [{self.resp.status_code}] {self.json}"

    @property
    def json_success(self) -> bool:
        if self.json:
            return self.json.get("success", False)
        return False


def _check_response(r: Response, session: Client) -> dict:
    if r.status_code >= 400:
        logger.info(f"Request failed. Bad status: {r.status_code}")
        raise APIError(r, session)

    try:
        json = r.json()
        logger.debug(f"Response with {json}")

        if json.get("error") is not None:  # {"error": "Произошла непредвиденная ошибка ..."}
            json["success"] = False
            json["kind"] = json["error"]

        if json.get("success", False) is False:
            logger.info("Request failed. Not success.")
            raise APIError(r, session, json=json)

        return json

    except JSONDecodeError:
        logger.info("Request failed. JSONDecodeError")
        raise APIError(r, session)


class DiaryApi:
    def __init__(self, host: str, session: Client, sessionid: str, user_information: dict):
        self._host = host
        self._session = session
        self.sessionid = sessionid
        self.user_information = user_information
        self.user = types.LoginObject.reformat(user_information)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
        self.close_session()

    def __repr__(self) -> str:
        return f"<DiaryApi {self.user.id}>"

    def close_session(self) -> None:
        logger.info(f"Closing DiaryApi {self.user.fio}")
        self._session.close()

    def _post(
        self, cls: Type[types.ObjectType], endpoint: str, data: Optional[dict] = None
    ) -> types.ObjectType:
        logger.debug(f'Request "{endpoint}" with data {data}')
        r = self._session.post(f"https://{self._host}/rest/{endpoint}", data=data)
        json = _check_response(r, self._session)
        return cls.reformat(json)

    @classmethod
    def auth_by_diary_session(
        cls, host: str, diary_session: str, diary_information: dict
    ) -> "DiaryApi":
        session = Client(
            headers={"User-Agent": USER_AGENT}, cookies={"sessionid": diary_session}, verify=False
        )
        return cls(host, session, diary_session, diary_information)

    @classmethod
    def auth_by_login(cls, host: str, login: str, password: str) -> "DiaryApi":
        logger.debug('Request "login" with data {"login": ..., "password": ...}')
        session = Client(headers={"User-Agent": USER_AGENT}, verify=False)
        r = session.get(f"https://{host}/rest/login?login={login}&password={password}")
        json = _check_response(r, session)
        diary_cookie = r.cookies.get("sessionid")
        if not diary_cookie:
            raise ValueError("Authorization failed. No cookie.")

        return cls(host, session, diary_cookie, json)

    def diary(
        self, from_date: str, to_date: Optional[str] = None, *, child: int = 0
    ) -> types.DiaryObject:
        if to_date is None:
            to_date = from_date

        return self._post(
            types.DiaryObject,
            "diary",
            {
                "pupil_id": self.user.children[child].id,
                "from_date": from_date,
                "to_date": to_date,
            },
        )

    def progress_average(self, date: str, *, child: int = 0) -> types.ProgressAverageObject:
        return self._post(
            types.ProgressAverageObject,
            "progress_average",
            {"pupil_id": self.user.children[child].id, "date": date},
        )

    def additional_materials(
        self, lesson_id: int, *, child: int = 0
    ) -> types.AdditionalMaterialsObject:
        return self._post(
            types.AdditionalMaterialsObject,
            "additional_materials",
            {"pupil_id": self.user.children[child].id, "lesson_id": lesson_id},
        )

    def school_meetings(self, *, child: int = 0) -> types.SchoolMeetingsObject:
        return self._post(
            types.SchoolMeetingsObject,
            "school_meetings",
            {"pupil_id": self.user.children[child].id},
        )

    def totals(self, date: str, *, child: int = 0) -> types.TotalsObject:
        return self._post(
            types.TotalsObject,
            "totals",
            {"pupil_id": self.user.children[child].id, "date": date},
        )

    def lessons_scores(
        self, date: str, subject: Optional[str] = None, *, child: int = 0
    ) -> types.LessonsScoreObject:
        if subject is None:
            subject = ""

        return self._post(
            types.LessonsScoreObject,
            "lessons_scores",
            {
                "pupil_id": self.user.children[child].id,
                "date": date,
                "subject": subject,
            },
        )

    def logout(self) -> types.BaseResponse:
        return self._post(types.BaseResponse, "logout")

    def check_food(self) -> types.CheckFoodObject:
        logger.debug('Request "check_food" with data None')
        r = self._session.post(f"https://{self._host}/rest/check_food")
        json = _check_response(r, self._session)
        return types.CheckFoodObject.parse_obj(json)


__all__ = (
    "DiaryApi",
    "APIError",
)
