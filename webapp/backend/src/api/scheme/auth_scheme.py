from pydantic import BaseModel, EmailStr, Field

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
