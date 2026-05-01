from dataclasses import dataclass


@dataclass
class ContactInfo:
    telegram: str | None = None
    phone: str | None = None
    facebook: str | None = None
