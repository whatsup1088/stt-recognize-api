from typing import Dict, List, Optional

from pydantic import BaseModel


class RecognitionModel(BaseModel):
    error: bool = False
    error_msg: str = ""
    data: Dict = {}
