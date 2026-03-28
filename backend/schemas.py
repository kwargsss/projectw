from pydantic import BaseModel
from typing import Optional, List

class RoleUpdate(BaseModel):
    user_id: int
    role: str

class EmbedField(BaseModel):
    name: str
    value: str
    inline: bool = False

class EmbedStructure(BaseModel):
    channel_id: str
    content: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[str] = "#5865F2"
    author_name: Optional[str] = None
    author_icon: Optional[str] = None
    author_url: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    fields: Optional[List[EmbedField]] = []

class EmbedBlock(BaseModel):
    type: str
    content: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    button_label: Optional[str] = None
    button_url: Optional[str] = None

class EmbedV2Structure(BaseModel):
    channel_id: str
    color: Optional[str] = "#5865F2"
    blocks: List[EmbedBlock] = []

class NotificationConfig(BaseModel):
    enabled: bool = False
    channel_id: str = ""
    embed_type: str = "v1"
    content: Optional[str] = ""
    title: Optional[str] = ""
    description: Optional[str] = ""
    color: Optional[str] = "#5865F2"
    image_url: Optional[str] = ""
    thumbnail_url: Optional[str] = ""
    blocks: List[EmbedBlock] = []

class NotificationSettingsModel(BaseModel):
    welcome: NotificationConfig
    goodbye: NotificationConfig