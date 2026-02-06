from pydantic import BaseModel, ConfigDict, Field


class UserSettingsCreate(BaseModel):
    notion_api_key: str = Field(..., min_length=1)


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    notion_api_key: str | None
