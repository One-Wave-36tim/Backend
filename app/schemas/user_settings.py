from pydantic import BaseModel


class UserSettingsCreate(BaseModel):
    notion_api_key: str


class UserSettingsResponse(BaseModel):
    success: bool
    user_id: int
    notion_api_key: str
