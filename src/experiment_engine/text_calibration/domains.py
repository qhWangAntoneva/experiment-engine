"""Pre-built keyword dictionaries and default conditions for 5 text domains.

Each domain provides a set of typical QCA conditions with associated Chinese
keywords used in citizen-government interaction texts.
"""

from __future__ import annotations

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConditionDefinition,
    ConditionSet,
    KeywordEntry,
    TextDomain,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Domain keyword presets
# ═══════════════════════════════════════════════════════════════════════════

DOMAIN_PRESETS: dict[TextDomain, dict[str, list[tuple[str, float]]]] = {
    TextDomain.DISSATISFACTION: {
        "strong_negative_affect": [
            ("非常不满", 1.0),
            ("太差了", 0.9),
            ("失望", 0.7),
            ("糟糕", 0.7),
            ("投诉", 0.6),
            ("举报", 0.8),
            ("愤怒", 0.9),
            ("无法接受", 0.8),
            ("受不了", 0.7),
            ("忍无可忍", 1.0),
            ("严重不满", 0.9),
            ("强烈谴责", 0.8),
        ],
        "service_failure_mention": [
            ("办不成", 1.0),
            ("没办成", 0.9),
            ("跑了好几趟", 0.8),
            ("效率低", 0.7),
            ("拖延", 0.7),
            ("不作为", 0.8),
            ("推诿", 0.8),
            ("踢皮球", 0.9),
            ("不予办理", 0.9),
            ("工作人员", 0.5),
            ("窗口", 0.4),
            ("排队", 0.4),
            ("态度差", 0.7),
            ("不专业", 0.6),
        ],
        "urgency_expression": [
            ("急", 0.6),
            ("立即", 0.8),
            ("马上", 0.7),
            ("尽快", 0.6),
            ("紧急", 1.0),
            ("迫在眉睫", 0.9),
            ("不能再等", 0.9),
            ("耽误不起", 0.8),
            ("急需", 0.8),
        ],
        "comparative_complaint": [
            ("别的地方", 0.6),
            ("其他部门", 0.6),
            ("别处", 0.5),
            ("人家", 0.4),
            ("凭什么", 0.7),
            ("不公平", 0.8),
            ("为什么别人", 0.8),
        ],
        "escalation_threat": [
            ("上级", 0.7),
            ("纪委", 0.9),
            ("信访", 0.8),
            ("曝光", 0.8),
            ("媒体", 0.7),
            ("市长热线", 0.9),
            ("中央", 0.8),
            ("省政府", 0.7),
            ("找领导", 0.8),
        ],
        "high_dissatisfaction": [  # outcome
            ("严重", 0.5),
            ("太差", 0.7),
        ],
    },
    TextDomain.POLICY_DEMAND: {
        "specific_policy_proposal": [
            ("建议", 0.8),
            ("希望政府", 0.9),
            ("应当出台", 0.9),
            ("应该设立", 0.9),
            ("制定政策", 0.9),
            ("修改规定", 0.8),
            ("完善制度", 0.7),
        ],
        "resource_request": [
            ("资金", 0.8),
            ("补贴", 0.8),
            ("拨款", 0.9),
            ("经费", 0.8),
            ("投入", 0.6),
            ("资助", 0.8),
            ("财政支持", 0.9),
        ],
        "group_representation": [
            ("我们群众", 0.8),
            ("大多数人", 0.7),
            ("代表大家", 0.9),
            ("老百姓", 0.7),
            ("全体居民", 0.9),
            ("广大", 0.6),
            ("我们这些人", 0.8),
        ],
        "evidence_citation": [
            ("根据", 0.6),
            ("数据显示", 0.9),
            ("据统计", 0.9),
            ("研究表明", 0.9),
            ("实际情况", 0.7),
        ],
        "feasibility_argument": [
            ("可以做到", 0.8),
            ("不难实现", 0.8),
            ("已有先例", 0.9),
            ("其他城市", 0.7),
            ("有条件的", 0.7),
            ("可行的", 0.8),
        ],
        "strong_policy_demand": [  # outcome
            ("强烈要求", 1.0),
            ("呼吁", 0.7),
            ("迫切需要", 0.9),
        ],
    },
    TextDomain.CO_PRODUCTION: {
        "willingness_to_participate": [
            ("我愿意", 0.9),
            ("积极参加", 0.9),
            ("配合", 0.7),
            ("支持", 0.5),
            ("协助", 0.8),
            ("志愿", 0.8),
            ("贡献力量", 0.9),
        ],
        "resource_contribution_offer": [
            ("提供", 0.6),
            ("出资", 0.9),
            ("出力", 0.9),
            ("投入", 0.6),
            ("捐赠", 0.9),
            ("贡献", 0.7),
            ("共享", 0.7),
        ],
        "knowledge_sharing": [
            ("我知道", 0.6),
            ("据我了解", 0.7),
            ("我的经验", 0.8),
            ("专业知识", 0.8),
            ("技术建议", 0.9),
            ("信息共享", 0.9),
        ],
        "collective_action_call": [
            ("大家一起", 0.9),
            ("齐心协力", 0.9),
            ("共同", 0.7),
            ("发动", 0.7),
            ("组织起来", 0.9),
            ("联合", 0.8),
        ],
        "co_production_request": [  # outcome
            ("共建", 0.9),
            ("合作", 0.7),
            ("协同", 0.8),
            ("参与治理", 0.9),
        ],
    },
    TextDomain.TRUST: {
        "institutional_trust": [
            ("相信政府", 0.9),
            ("信任", 0.7),
            ("可靠", 0.7),
            ("公信力", 0.8),
            ("值得信赖", 0.9),
        ],
        "competence_perception": [
            ("有能力", 0.8),
            ("专业", 0.6),
            ("效率高", 0.7),
            ("办事得力", 0.9),
            ("解决得好", 0.8),
        ],
        "benevolence_perception": [
            ("为老百姓着想", 0.9),
            ("关心群众", 0.9),
            ("贴心", 0.8),
            ("人性化", 0.7),
            ("温暖", 0.6),
        ],
        "integrity_perception": [
            ("公正", 0.8),
            ("透明", 0.7),
            ("廉洁", 0.9),
            ("按规定办事", 0.8),
            ("公开", 0.6),
        ],
        "positive_experience_share": [
            ("好评", 0.7),
            ("满意", 0.6),
            ("感谢", 0.5),
            ("表扬", 0.8),
            ("点赞", 0.7),
            ("值得肯定", 0.8),
        ],
        "high_trust": [  # outcome
            ("很信任", 0.9),
            ("放心", 0.7),
        ],
    },
    TextDomain.GOV_RESPONSIVENESS: {
        "response_timeliness": [
            ("及时", 0.7),
            ("迅速", 0.8),
            ("马上回复", 0.9),
            ("当天", 0.7),
            ("很快", 0.6),
            ("三天内", 0.8),
        ],
        "solution_effectiveness": [
            ("解决了", 0.9),
            ("办好了", 0.9),
            ("处理完毕", 0.9),
            ("落实到位", 0.9),
            ("已经落实", 0.9),
        ],
        "process_transparency": [
            ("公开", 0.7),
            ("公示", 0.8),
            ("告知", 0.6),
            ("说明了", 0.7),
            ("解释清楚", 0.8),
            ("结果反馈", 0.9),
        ],
        "interaction_quality": [
            ("态度好", 0.7),
            ("耐心", 0.7),
            ("热情", 0.7),
            ("认真", 0.6),
            ("细心", 0.7),
        ],
        "follow_up_mechanism": [
            ("回访", 0.8),
            ("后续跟进", 0.9),
            ("定期", 0.6),
            ("跟踪", 0.7),
            ("持续关注", 0.8),
        ],
        "high_responsiveness": [  # outcome
            ("非常负责", 0.9),
            ("响应及时", 0.8),
            ("效率很高", 0.7),
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  Default calibration params (overridable via training or manual config)
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CALIBRATION = CalibrationParams(
    threshold_full_in=0.80,
    threshold_full_out=0.20,
    crossover_point=0.50,
    direction="ascending",
)


# ═══════════════════════════════════════════════════════════════════════════
#  Builder function
# ═══════════════════════════════════════════════════════════════════════════


def build_default_conditions(
    domain: TextDomain,
    calibration_type: CalibrationType = CalibrationType.DIRECT,
) -> ConditionSet:
    """Build a default :class:`ConditionSet` for a given text domain.

    Returns a fully configured ConditionSet with pre-built keyword dictionaries
    and default calibration parameters. The last entry in each domain preset
    is treated as the outcome condition.

    Args:
        domain: The text domain to build conditions for.
        calibration_type: Calibration method for all conditions.

    Returns:
        A ConditionSet ready for use or further customization.
    """
    preset = DOMAIN_PRESETS.get(domain)
    if preset is None:
        raise ValueError(f"Unknown domain: {domain}")

    condition_names = list(preset.keys())
    outcome_name = condition_names[-1]
    causal_names = condition_names[:-1]

    conditions: list[ConditionDefinition] = []
    for name in causal_names:
        keywords = [KeywordEntry(pattern=kw, weight=w) for kw, w in preset[name]]
        conditions.append(
            ConditionDefinition(
                name=name,
                display_name=name,
                domain=domain,
                keywords=keywords,
                calibration_type=calibration_type,
                calibration_params=DEFAULT_CALIBRATION,
            )
        )

    outcome_keywords = [
        KeywordEntry(pattern=kw, weight=w) for kw, w in preset[outcome_name]
    ]
    outcome = ConditionDefinition(
        name=outcome_name,
        display_name=outcome_name,
        domain=domain,
        keywords=outcome_keywords,
        calibration_type=calibration_type,
        calibration_params=DEFAULT_CALIBRATION,
    )

    return ConditionSet(
        name=f"{domain.value}_default",
        description=f"Default QCA conditions for {domain.value} domain",
        conditions=conditions,
        outcome=outcome,
        domain=domain,
    )
