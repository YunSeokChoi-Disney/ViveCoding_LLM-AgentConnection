from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=100)
    nickname: str = Field(min_length=1, max_length=50)


class SignupResponse(BaseModel):
    id: int
    username: str
    nickname: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nickname: str


class WithdrawResponse(BaseModel):
    message: str


class NpcChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class NpcChatResponse(BaseModel):
    reply: str


class NpcResetResponse(BaseModel):
    message: str
