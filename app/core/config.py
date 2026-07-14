from dataclasses import dataclass


@dataclass(slots=True)
class PipelineConfig:

    timeout: int = 60

    retries: int = 5

    page_size: int = 50

    request_delay: float = 0.3


settings = PipelineConfig()
