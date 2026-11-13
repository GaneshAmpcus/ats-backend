import enum


class CustomFieldEntity(str, enum.Enum):
    JOB = "JOB"
    CANDIDATE = "CANDIDATE"
    CLIENT = "CLIENT"


class CustomFieldType(str, enum.Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"
    DROPDOWN = "DROPDOWN"
    MULTI_SELECT = "MULTI_SELECT"
