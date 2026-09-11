from dataclasses import dataclass


class DaytonaExecutionError(RuntimeError):
    """An actionable failure when creating an isolated Daytona crew sandbox."""


@dataclass(frozen=True)
class DaytonaCrewRunner:
    api_key: str

    def create_sandbox(self) -> object:
        try:
            from daytona import Daytona, DaytonaConfig

            client = Daytona(DaytonaConfig(api_key=self.api_key))
            return client.create()
        except ImportError as error:
            raise DaytonaExecutionError("The Daytona SDK is not installed.") from error
