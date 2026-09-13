from typing import Literal

from pydantic import BaseModel, ConfigDict


class AccountDeletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: Literal["DELETE"]


class AccountDeletionResponse(BaseModel):
    deleted: bool
    preferences_deleted: int
    paper_accounts_deleted: int
    paper_orders_deleted: int
    broker_orders_deleted: int
