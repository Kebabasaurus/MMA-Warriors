"""Explicit ordered concatenation: do not regroup historical batches."""
from dataclasses import replace
from ..followup_expansion import LEGACY_FOLLOWUP_UPDATES
from ..followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from ..followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from .punches import BATCH_001
from .power_punch_development import POWER_PUNCH_DEVELOPMENT
from .jab_development import JAB_DEVELOPMENT
from .kick_development import SLICE_5_KICKS
from .clinch_development import CLINCH_DEVELOPMENT
from .wrestling_development import WRESTLING_DEVELOPMENT
from .ground_top_development import GROUND_TOP_DEVELOPMENT
from .bottom_submission_development import BOTTOM_SUBMISSION_DEVELOPMENT
from .kicks import BATCH_002
from .punches import BATCH_003
from .style_signatures import BATCH_004
from .takedowns import BATCH_005
from .clinch import BATCH_006
from .takedowns import BATCH_007
from .clinch import BATCH_008
from .escapes import BATCH_009
from .takedowns import BATCH_010
from .scrambles import BATCH_011
from .ground_control import BATCH_012
from .passes import BATCH_013
from .scrambles import BATCH_014
from .escapes import BATCH_015
from .scrambles import BATCH_016
from .escapes import BATCH_017
from .submissions import BATCH_018
from .scrambles import BATCH_019
from .submissions import BATCH_020
from .scrambles import BATCH_021
from .ground_control import BATCH_022
from .escapes import BATCH_023
from .ground_control import BATCH_024
from .escapes import BATCH_025
from .clinch import BATCH_026
from .punches import BATCH_027
from .clinch import BATCH_028
from .scrambles import BATCH_029
from .top_submissions import PHASE_29
from .bottom_development import PHASE_30

MOVE_DEFINITIONS = (
    BATCH_001
    + BATCH_002
    + BATCH_003
    + BATCH_004
    + BATCH_005
    + BATCH_006
    + BATCH_007
    + BATCH_008
    + BATCH_009
    + BATCH_010
    + BATCH_011
    + BATCH_012
    + BATCH_013
    + BATCH_014
    + BATCH_015
    + BATCH_016
    + BATCH_017
    + BATCH_018
    + BATCH_019
    + BATCH_020
    + BATCH_021
    + BATCH_022
    + BATCH_023
    + BATCH_024
    + BATCH_025
    + BATCH_026
    + BATCH_027
    + BATCH_028
    + BATCH_029
    + PHASE_29
    + PHASE_30
    + POWER_PUNCH_DEVELOPMENT
    + JAB_DEVELOPMENT
    + SLICE_5_KICKS
    + CLINCH_DEVELOPMENT
    + WRESTLING_DEVELOPMENT
    + GROUND_TOP_DEVELOPMENT
    + BOTTOM_SUBMISSION_DEVELOPMENT
)

# Audited successor-only migration; historical literals remain independently reviewable.
MOVE_DEFINITIONS = tuple(
    replace(move, follow_ups=LEGACY_FOLLOWUP_UPDATES[move.move_id])
    if move.move_id in LEGACY_FOLLOWUP_UPDATES else move
    for move in MOVE_DEFINITIONS
)

# A separately source-bound action-diversity layer preserves the reviewed 125-map.
MOVE_DEFINITIONS = tuple(
    replace(move, follow_ups=ACTION_DIVERSE_FOLLOWUP_UPDATES[move.move_id])
    if move.move_id in ACTION_DIVERSE_FOLLOWUP_UPDATES else move
    for move in MOVE_DEFINITIONS
)

# Second reviewed action-diversity layer; each historical layer keeps its own manifest.
MOVE_DEFINITIONS = tuple(
    replace(move, follow_ups=CONTINUITY_FOLLOWUP_UPDATES[move.move_id])
    if move.move_id in CONTINUITY_FOLLOWUP_UPDATES else move
    for move in MOVE_DEFINITIONS
)
