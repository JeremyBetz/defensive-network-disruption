"""Experimental provider-independent local attacking-option networks.

Importing this namespace performs no data loading, downloading, plotting, or
analysis. Option shares are conditional-model outputs, not accessibility truth.
"""

from defensive_network_disruption.data.option_adapter import (
    MetricCoordinateContext,
    option_state_from_kloppy,
)
from defensive_network_disruption.networks.options import (
    FrozenOptionModel,
    OptionEdge,
    OptionNetwork,
    OptionState,
    compare_options,
    evaluate_options,
)
from defensive_network_disruption.visualization.options import (
    animate_option_network_comparison,
    plot_option_network,
)

__all__ = (
    "FrozenOptionModel",
    "MetricCoordinateContext",
    "OptionEdge",
    "OptionNetwork",
    "OptionState",
    "animate_option_network_comparison",
    "compare_options",
    "evaluate_options",
    "option_state_from_kloppy",
    "plot_option_network",
)
