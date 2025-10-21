"""
智能体模块
包含所有智能体的实现
"""

from .hotspot_agent import (
    Hotspot,
    create_hotspot_agent,
    parse_hotspot_response,
    filter_hotspots_by_heat,
    sort_hotspots_by_heat,
    get_hotspots_by_category,
    export_hotspots_to_json
)

from .analysis_agent import (
    AnalysisReport,
    create_analysis_agent,
    parse_analysis_response,
    export_analysis_to_json,
    get_sentiment_label,
    calculate_audience_score
)

from .content_agent import (
    Content,
    create_content_agent,
    parse_content_response,
    export_contents_to_json,
    get_content_by_platform,
    filter_contents_by_word_count,
    get_content_statistics,
    validate_all_contents,
    create_content_summary
)

__all__ = [
    # hotspot_agent
    'Hotspot',
    'create_hotspot_agent',
    'parse_hotspot_response',
    'filter_hotspots_by_heat',
    'sort_hotspots_by_heat',
    'get_hotspots_by_category',
    'export_hotspots_to_json',
    # analysis_agent
    'AnalysisReport',
    'create_analysis_agent',
    'parse_analysis_response',
    'export_analysis_to_json',
    'get_sentiment_label',
    'calculate_audience_score',
    # content_agent
    'Content',
    'create_content_agent',
    'parse_content_response',
    'export_contents_to_json',
    'get_content_by_platform',
    'filter_contents_by_word_count',
    'get_content_statistics',
    'validate_all_contents',
    'create_content_summary',
]
