
class Features:
    DASHBOARD = "dashboard"

    @classmethod
    def all(cls) -> list[str]:
        return [cls.DASHBOARD]

    @classmethod
    def is_valid(cls, feature: str) -> bool:
        return feature in cls.all()
