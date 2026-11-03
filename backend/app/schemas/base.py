from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    # Rule 2: the LLM returns JSON, so a stray key must fail loudly instead of being dropped.
    # NaN and Infinity would otherwise reach the .tex as font sizes and fail to compile.
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
