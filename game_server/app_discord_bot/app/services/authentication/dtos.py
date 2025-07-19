from dataclasses import dataclass

@dataclass
class RegistrationResultDTO:
    invite_link: str
    public_message: str