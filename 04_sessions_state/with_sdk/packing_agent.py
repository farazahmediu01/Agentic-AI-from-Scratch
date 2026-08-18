"""
The demo agent for Chapter 4's three observation scripts.

    session_demo.py   what a session actually holds, and what session_id scopes
    growth_demo.py    what a session costs, measured
    context_demo.py   what a context is, and what the model can never see

DELIBERATELY NOT EXPENSES. Every chapter's `with_sdk/` layer before this one
demonstrated on the spine, and that was fine while the capability WAS the spine's
next feature. Sessions are not: they are a property of any conversation at all.
Watching memory work on luggage, then watching it work on Spendly, is the
difference between learning what a session does and learning what Spendly does.

The domain is packing for a trip. It was chosen for one property: **the second
turn is meaningless without the first.** "Add two more" is not a sentence a
stateless agent can act on, and that is precisely what we are here to see.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents import Agent, RunContextWrapper, function_tool

# No path juggling for this one: `shared` is a real installed package (see the
# [build-system] block in pyproject.toml), which is exactly why it was made one.
from shared.models import make_model

__all__ = ["Traveller", "agent", "packing_agent"]


@dataclass
class Traveller:
    """
    Who we are packing for. A context object, and nothing more than that.

    `packed` being IN here rather than in a module-level list is worth pausing
    on. It means two travellers running through the same agent cannot see each
    other's suitcase, without a single line of code enforcing it -- the isolation
    is a consequence of the object graph, not of a check somebody remembered to
    write. That is what dependency injection buys, and it is why "just use a
    global" stops working the moment there are two of anyone.
    """

    name: str
    bag_limit_kg: float
    packed: list[tuple[str, float]] = field(default_factory=list)

    @property
    def packed_kg(self) -> float:
        return round(sum(kg for _, kg in self.packed), 2)


@function_tool
def whoami(ctx: RunContextWrapper[Traveller]) -> str:
    """Who this bag is being packed for, and what their airline allowance is."""
    # THE TOOL THAT PROVES THE POINT.
    #
    # The model has never been told this traveller's name. It is not in the
    # instructions, not in the user's message, and -- run session_demo.py and
    # check -- not anywhere in the session's stored items either.
    #
    # The ONLY way a name reaches the model is if a tool puts it there. That is
    # the boundary: a context is invisible until a tool chooses to reveal some
    # of it, and choosing what to reveal is a security decision you now get to
    # make on purpose instead of by accident.
    who = ctx.context
    return f"{who.name}, allowance {who.bag_limit_kg} kg"


@function_tool
def add_item(ctx: RunContextWrapper[Traveller], item: str, kg: float) -> str:
    """
    Put one item in the bag.

    Args:
        item: What to pack, e.g. 't-shirt'.
        kg: How much it weighs in kilograms.
    """
    # Tools may WRITE to the context, and the write is visible to the next tool
    # call in the same run. Whether it survives to the NEXT run is up to you: the
    # SDK hands whatever object you passed to `context=`, so if you keep the
    # reference, the state keeps. See context_demo.py.
    ctx.context.packed.append((item, kg))
    return f"Packed {item} ({kg} kg). Bag now {ctx.context.packed_kg} kg."


@function_tool
def remaining_allowance(ctx: RunContextWrapper[Traveller]) -> float:
    """How many kilograms are still free in this traveller's allowance."""
    return round(ctx.context.bag_limit_kg - ctx.context.packed_kg, 2)


@function_tool
def show_list(ctx: RunContextWrapper[Traveller]) -> str:
    """List everything packed so far."""
    if not ctx.context.packed:
        return "The bag is empty."
    return "; ".join(f"{item} ({kg} kg)" for item, kg in ctx.context.packed)


INSTRUCTIONS = """You help someone pack a suitcase for a trip.

- Use the tools for every fact. Never estimate a weight the tools can give you.
- If the user refers to something from earlier in the conversation ("two more of
  those", "the heavy one"), use what they said earlier. Do not ask again.
- If you genuinely do not know an item's weight, ask. Do not invent one.
- Keep replies to one short sentence."""

packing_agent = Agent[Traveller](
    name="Packing Assistant",
    instructions=INSTRUCTIONS,
    model=make_model(),
    tools=[whoami, add_item, remaining_allowance, show_list],
)

# A shorter alias, because three demo scripts import it.
agent = packing_agent
