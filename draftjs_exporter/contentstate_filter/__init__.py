"""Filter Draft.js ContentState with declarative rules."""

import copy
from collections.abc import Callable
from typing import Any, Literal, TypeAlias, TypedDict

from draftjs_exporter.constants import BLOCK_TYPES
from draftjs_exporter.error import ConfigException
from draftjs_exporter.types import Block, ContentState, Entity, InlineStyleRange

FilterCallback: TypeAlias = Callable[[Any], Any]
"""Custom rule action: receives the matched object, returns a replacement or None."""

FilterAction: TypeAlias = Literal["remove", "keep", "demote"] | FilterCallback
"""Predefined action name or custom callback."""


class FilterRule(TypedDict):
    """A single filtering rule."""

    type: Literal["block", "inline_style", "entity"]
    """Which kind of object the rule matches."""

    match: str
    """The block type, style name, or entity type to match."""

    action: FilterAction
    """What to do with matching objects."""


HEADER_DEMOTION = {
    BLOCK_TYPES.HEADER_ONE: BLOCK_TYPES.HEADER_TWO,
    BLOCK_TYPES.HEADER_TWO: BLOCK_TYPES.HEADER_THREE,
    BLOCK_TYPES.HEADER_THREE: BLOCK_TYPES.HEADER_FOUR,
    BLOCK_TYPES.HEADER_FOUR: BLOCK_TYPES.HEADER_FIVE,
    BLOCK_TYPES.HEADER_FIVE: BLOCK_TYPES.HEADER_SIX,
}
"""Heading demotion targets. ``header-six`` cannot be demoted."""

LIST_BLOCKS = frozenset(
    {BLOCK_TYPES.UNORDERED_LIST_ITEM, BLOCK_TYPES.ORDERED_LIST_ITEM}
)
"""Block types whose depth participates in list nesting."""

VALID_ACTIONS = frozenset({"remove", "keep", "demote"})


class ContentStateFilter:
    """Apply declarative rules to a ContentState.

    Rules run in definition order per object. Objects without a
    matching rule are kept. The filter always produces a structurally
    valid ContentState: entity ranges and the entity map stay in sync,
    and list depths are re-normalized after removals.
    """

    __slots__ = ("rules",)

    def __init__(self, rules: list[FilterRule] | None = None) -> None:
        """Initialize the filter, validating rules eagerly.

        Parameters:
            rules: The rules to apply, in order.

        Raises:
            ConfigException: If a rule is malformed.
        """
        self.rules = rules if rules is not None else []
        for rule in self.rules:
            self._validate(rule)

    @staticmethod
    def _validate(rule: FilterRule) -> None:
        """Check a rule for structural validity.

        Parameters:
            rule: The rule to validate.

        Raises:
            ConfigException: If the rule type or action is invalid.
        """
        if rule["type"] not in ("block", "inline_style", "entity"):
            raise ConfigException(f"Invalid filter rule type: {rule['type']!r}")
        action = rule["action"]
        if not callable(action) and action not in VALID_ACTIONS:
            raise ConfigException(f"Invalid filter rule action: {action!r}")
        if action == "demote" and (
            rule["type"] != "block" or rule["match"] not in HEADER_DEMOTION
        ):
            raise ConfigException(
                '"demote" only applies to header-one through header-five blocks'
            )

    def apply(self, content_state: ContentState) -> ContentState:
        """Apply all rules, returning a new ContentState.

        Parameters:
            content_state: The ContentState to filter. Not mutated.

        Returns:
            The filtered ContentState.
        """
        entity_map_in = content_state.get("entityMap", {})
        block_rules = self._rules_by_match("block")
        style_rules = self._rules_by_match("inline_style")
        entity_rules = self._rules_by_match("entity")

        out_blocks: list[Block] = []
        replacements: dict[str, Entity] = {}
        used_keys: set[str] = set()

        for block in content_state.get("blocks", []):
            kept = self._apply_block_rule(copy.deepcopy(block), block_rules)
            if kept is None:
                continue
            self._apply_style_rules(kept, style_rules)
            self._apply_entity_rules(
                kept, entity_map_in, entity_rules, replacements, used_keys
            )
            out_blocks.append(kept)

        self._normalize_depths(out_blocks)

        entity_map_out = {}
        for key in used_keys:
            entity = replacements.get(key, entity_map_in[key])
            entity_map_out[key] = entity
        return {"blocks": out_blocks, "entityMap": entity_map_out}

    def _rules_by_match(self, kind: str) -> dict[str, list[FilterAction]]:
        """Group actions for a rule kind by match value."""
        grouped: dict[str, list[FilterAction]] = {}
        for rule in self.rules:
            if rule["type"] == kind:
                grouped.setdefault(rule["match"], []).append(rule["action"])
        return grouped

    @staticmethod
    def _run_actions(value: Any, actions: list[FilterAction], kind: str) -> Any:
        """Run a chain of actions over a matched object.

        Parameters:
            value: The matched object.
            actions: The actions to run in order.
            kind: Rule kind, for error messages.

        Returns:
            The transformed object, or None when removed.

        Raises:
            ConfigException: If a callback returns an invalid value.
        """
        current = value
        for action in actions:
            if current is None:
                break
            if action == "keep":
                continue
            if action == "remove":
                current = None
                continue
            if action == "demote":
                if not isinstance(current, dict) or current.get("type") not in (
                    HEADER_DEMOTION
                ):
                    raise ConfigException(
                        "Filter callback must return a demotable header block"
                    )
                current = {**current, "type": HEADER_DEMOTION[current["type"]]}
                continue
            current = action(current)
            valid = (
                current is None
                or (kind == "inline_style" and isinstance(current, str))
                or (kind != "inline_style" and isinstance(current, dict))
            )
            if not valid:
                raise ConfigException(
                    f"Filter callback for {kind} rule returned invalid value"
                )
        return current

    def _apply_block_rule(
        self, block: Block, rules: dict[str, list[FilterAction]]
    ) -> Block | None:
        """Apply block rules to a single block."""
        actions = rules.get(block.get("type", ""), [])
        if not actions:
            return block
        result = self._run_actions(block, actions, "block")
        if result is not None and "type" not in result:
            raise ConfigException("Filter block callback must return a block")
        return result

    def _apply_style_rules(
        self, block: Block, rules: dict[str, list[FilterAction]]
    ) -> None:
        """Apply inline style rules to a block's style ranges."""
        ranges = block.get("inlineStyleRanges", [])
        if not ranges or not rules:
            return
        kept: list[InlineStyleRange] = []
        for style_range in ranges:
            actions = rules.get(style_range["style"], [])
            if not actions:
                kept.append(style_range)
                continue
            result = self._run_actions(style_range["style"], actions, "inline_style")
            if result is not None:
                kept.append(
                    {
                        "offset": style_range["offset"],
                        "length": style_range["length"],
                        "style": result,
                    }
                )
        block["inlineStyleRanges"] = kept

    def _apply_entity_rules(
        self,
        block: Block,
        entity_map: dict[str, Entity],
        rules: dict[str, list[FilterAction]],
        replacements: dict[str, Entity],
        used_keys: set[str],
    ) -> None:
        """Apply entity rules to a block's entity ranges."""
        kept = []
        for entity_range in block.get("entityRanges", []):
            key = str(entity_range["key"])
            entity = entity_map.get(key)
            if entity is None:
                # Orphaned range: drop to keep output valid.
                continue
            actions = rules.get(entity.get("type", ""), [])
            if not actions:
                kept.append(entity_range)
                used_keys.add(key)
                continue
            result = self._run_actions(copy.deepcopy(entity), actions, "entity")
            if result is not None:
                if "type" not in result:
                    raise ConfigException(
                        "Filter entity callback must return an entity"
                    )
                kept.append(entity_range)
                used_keys.add(key)
                replacements[key] = result
        block["entityRanges"] = kept

    @staticmethod
    def _normalize_depths(blocks: list[Block]) -> None:
        """Clamp list depths so nesting never skips a level.

        Parameters:
            blocks: Blocks to normalize in place.
        """
        last_list_depth = -1
        for block in blocks:
            if block.get("type") in LIST_BLOCKS:
                depth = block.get("depth", 0)
                if depth > last_list_depth + 1:
                    depth = last_list_depth + 1
                block["depth"] = depth
                last_list_depth = depth
            else:
                last_list_depth = -1
