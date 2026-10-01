from typing import Any, Dict

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    run_id: str = Field(..., min_length=1)

    sender: str = Field(..., min_length=1)
    receiver: str = Field(..., min_length=1)

    message_type: str = Field(..., min_length=1)

    payload: Dict[str, Any] = Field(default_factory=dict)