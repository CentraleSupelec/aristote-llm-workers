from typing import List, Optional

from pydantic import BaseModel


class TextDTO(BaseModel):
    text: str
    start: Optional[float] = None
    end: Optional[float] = None


class TranscribedText(TextDTO):
    pass


class Summary(TextDTO):
    pass


class MediaType(TextDTO):
    pass


class Reformulation(TextDTO):
    pass


class MetaData(BaseModel):
    title: str
    description: str
    discipline: Optional[str] = None
    media_type: Optional[str] = None
    main_topics: Optional[List[str]] = None
