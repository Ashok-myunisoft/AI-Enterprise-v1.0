from pydantic import BaseModel, ConfigDict
from typing import Optional , Dict , Any


class ExecuteRequest(BaseModel):
    tenantId: int
    userId: int
    initiativeCode: str
    botCode: str
    capabilityCode: str
    input: Dict[str, Any]

class ExecuteResponse(BaseModel):
    executionId: int
    result: Dict[str, Any]


class ExecutionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    AIexecutionid: int
    userid: Optional[int] = None
    tenantid: Optional[int] = None
    AIinitiativeid: Optional[int] = None
    AIbotid: Optional[int] = None
    AIcapabilityid: Optional[int] = None
    outcomestatus: Optional[int] = None
    inputpayload: Optional[Dict[str, Any]] = None
    outputpayload: Optional[Dict[str, Any]] = None
    sessionid: Optional[str] = None


