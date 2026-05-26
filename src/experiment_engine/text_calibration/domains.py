"""Pre-built prototype templates and default conditions for 5 text domains.

Each domain provides a set of typical QCA conditions with prototype text
templates used for BERT CLS embedding + cosine similarity scoring.
"""

from __future__ import annotations

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConceptPrototype,
    ConditionDefinition,
    ConditionSet,
    TextDomain,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Domain prototype text presets
# ═══════════════════════════════════════════════════════════════════════════

DOMAIN_PRESETS: dict[TextDomain, dict[str, list[dict[str, str | int | float]]]] = {
    TextDomain.DISSATISFACTION: {
        "strong_negative_affect": [
            {
                "prototype_text": "你们这服务太差了，态度恶劣，办事效率极低，我非常愤怒要投诉你们",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "请帮我查一下这个申请什么时候能办好，谢谢",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "service_failure_mention": [
            {
                "prototype_text": "我去办证跑了好几趟都没办成，窗口人员互相推诿踢皮球，不予办理",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "工作人员态度很好，耐心解答了我的问题，顺利办完了",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "urgency_expression": [
            {
                "prototype_text": "这个问题急需解决，迫在眉睫，不能再等了，耽误不起，请立即处理",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "慢慢来吧，等你们有空了再帮我处理一下就行",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "comparative_complaint": [
            {
                "prototype_text": "为什么别的地方能办我们这里就不行？凭什么区别对待，太不公平了",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我想了解一下这个业务的办理流程是什么",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "escalation_threat": [
            {
                "prototype_text": "如果再不解决我就打市长热线，找纪委和媒体曝光你们",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "希望能尽快帮我处理一下，我已经等了一周了",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "high_dissatisfaction": [  # outcome
            {
                "prototype_text": "你们的服务太差了，严重不作为，我对你们彻底失望",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "事情办完了，效率还可以，整体来说比较满意",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
    },
    TextDomain.POLICY_DEMAND: {
        "specific_policy_proposal": [
            {
                "prototype_text": "建议政府制定相关惠民政策，完善城市管理制度，修改不合理的旧规定",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我就想问一下现在这个政策具体是怎么执行的",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "resource_request": [
            {
                "prototype_text": "我们需要政府增加资金投入和财政支持，给老百姓发放更多补贴",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "这个政策很好，希望能够尽快落实到位",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "group_representation": [
            {
                "prototype_text": "我们全体居民代表大家反映这个问题，这是广大群众的共同心声",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我个人觉得这个政策对我们家影响挺大的",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "evidence_citation": [
            {
                "prototype_text": "据统计数据显示，研究表明这种做法在其他城市已有成功先例可以参考",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我觉得这个做法应该能行，大家都会支持的",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "feasibility_argument": [
            {
                "prototype_text": "这个方案是可以做到的，其他城市已有先例，条件完全具备，难度不大",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "这个事情太难了，我觉得根本不可能实现",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "strong_policy_demand": [  # outcome
            {
                "prototype_text": "我们强烈要求政府尽快出台相关政策，迫切需要解决这个问题",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "随便了解一下这个政策的具体内容是什么",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
    },
    TextDomain.CO_PRODUCTION: {
        "willingness_to_participate": [
            {
                "prototype_text": "我愿意积极参加社区治理工作，配合你们一起把这件事做好",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "这是政府该管的事，跟我们普通老百姓没什么关系",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "resource_contribution_offer": [
            {
                "prototype_text": "我们愿意出资出力，捐赠物资，提供必要资源来共同解决这个问题",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "你们政府自己想办法解决，我们没钱也没资源",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "knowledge_sharing": [
            {
                "prototype_text": "据我了解和我多年经验，我从专业角度提几点技术建议和信息共享",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我不太懂这些，你们专业人士看着办就行",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "collective_action_call": [
            {
                "prototype_text": "大家一起齐心协力，组织起来联合行动，共同把这事办好",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我一个人来反映一下意见就行了，不需要别人一起",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "co_production_request": [  # outcome
            {
                "prototype_text": "我们希望与政府合作共建，协同推动社区参与治理",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "请帮我查询一下这个文件的具体办理进度",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
    },
    TextDomain.TRUST: {
        "institutional_trust": [
            {
                "prototype_text": "我相信政府一定能把这件事处理好，政府办事越来越可靠值得信赖",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "政府没什么公信力，我不相信他们能解决好这个问题",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "competence_perception": [
            {
                "prototype_text": "工作人员非常专业能力强，办事效率高，解决得特别好很得力",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "办事人员不专业，连基本政策都解释不清楚",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "benevolence_perception": [
            {
                "prototype_text": "政府真心为老百姓着想，关心群众生活，政策很贴心很人性化",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "政府根本不关心我们的实际困难，只顾自己方便",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "integrity_perception": [
            {
                "prototype_text": "工作人员按规定办事，公正透明，廉洁高效，全程公开",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "这里面肯定有猫腻，不按规矩来，关系户优先",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "positive_experience_share": [
            {
                "prototype_text": "我要表扬他们，服务态度很好，值得点赞，非常满意，值得肯定",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "服务太差了，我一点都不满意，必须给你们差评",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "high_trust": [  # outcome
            {
                "prototype_text": "我对政府很信任，办事很放心，相信他们会公正处理",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "我对政府完全不信任，每次办事都不放心",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
    },
    TextDomain.GOV_RESPONSIVENESS: {
        "response_timeliness": [
            {
                "prototype_text": "当天就回复了，处理速度很快，三个工作日内就全部办完了",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "等了好几天也没个回复，到现在都不知道进展怎么样了",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "solution_effectiveness": [
            {
                "prototype_text": "问题已经解决了，办好了，处理非常到位，落实得很好很彻底",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "虽然回复了但是问题根本没解决，敷衍了事",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "process_transparency": [
            {
                "prototype_text": "整个过程都公开公示了，每一步都告知我们，解释得很清楚有结果反馈",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "什么信息都不公开，问了好几次也不告诉我们进展",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "interaction_quality": [
            {
                "prototype_text": "工作人员态度好很有耐心，认真细致，热情周到，服务非常贴心",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "工作人员态度冷漠，问三句答一句，一副不耐烦的样子",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "follow_up_mechanism": [
            {
                "prototype_text": "办理后还有回访电话，后续跟进做得很到位，持续关注我们的情况",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "办完就完了，没有任何后续跟进，出了问题也不知道找谁",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
        "high_responsiveness": [  # outcome
            {
                "prototype_text": "政府非常负责，响应非常及时，处理效率很高，我们很满意",
                "is_member": 1,
                "weight": 1.0,
            },
            {
                "prototype_text": "投诉了也没用，根本没人管，效率太低了",
                "is_member": 0,
                "weight": 1.0,
            },
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

    Returns a fully configured ConditionSet with pre-built prototype text
    templates and default calibration parameters. The last entry in each
    domain preset is treated as the outcome condition.

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
        proto_entries = preset[name]
        prototypes = [
            ConceptPrototype(
                prototype_text=p["prototype_text"],
                is_member=p["is_member"],
                weight=p.get("weight", 1.0),
            )
            for p in proto_entries
        ]
        conditions.append(
            ConditionDefinition(
                name=name,
                display_name=name,
                domain=domain,
                prototypes=prototypes,
                calibration_type=calibration_type,
                calibration_params=DEFAULT_CALIBRATION,
            )
        )

    outcome_proto_entries = preset[outcome_name]
    outcome_prototypes = [
        ConceptPrototype(
            prototype_text=p["prototype_text"],
            is_member=p["is_member"],
            weight=p.get("weight", 1.0),
        )
        for p in outcome_proto_entries
    ]
    outcome = ConditionDefinition(
        name=outcome_name,
        display_name=outcome_name,
        domain=domain,
        prototypes=outcome_prototypes,
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
