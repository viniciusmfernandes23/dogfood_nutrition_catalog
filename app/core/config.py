from dataclasses import dataclass


@dataclass(slots=True)
class PipelineConfig:

    timeout: int = 30

    retries: int = 3

    page_size: int = 50

    request_delay: float = 0.3


settings = PipelineConfig()