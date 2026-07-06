from dataclasses import dataclass


@dataclass(slots=True)

class PriceCategory:

    availability: str

    price_status: str

    price_per_kg_status: str

    subscriber_status: str