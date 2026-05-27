"""
Prototype Usage Samples — 3 组可分析的 prototype usage samples

每组包含:
  1. CSV 数据文本 (text_id,domain,text,expected_outcome)
  2. 对应的 condition_set YAML dict (可直接被 _condition_set_from_dict() 消费)
  3. 测试说明注释

使用方法:
  uv run python scripts/prototype_usage_samples.py

这 3 组 sample 覆盖了以下代码路径:
  Sample 1 — handle_calibrate(prototype_texts_path=...) 分支
  Sample 2 — CosineSimilarityEngine positive-only edge case + 非 1.0 weight
  Sample 3 — handle_embed_calibrate(embedding-based) 路径

重要原则 (Do-Not-Repeat):
  - CSV 必须包含 expected_outcome 列 (避免从 trigram 推算)
  - 所有校准必须使用 process() 批处理 (避免 calibrate_one 逐条 → min==max 退化)
  - YAML 字符串必须先 yamlToConditionSet() 解析再传 (避免被当 raw object 传)
  - 中文文本写入 VFS 必须用 TextEncoder + Uint8Array (避免零字节文件)
  - 所有 Python open() 必须显式 encoding='utf-8'
  - 文本内容必须有足够变异 (避免所有文本触发 min==max 退化分支)
"""
# ruff: noqa
# ═══════════════════════════════════════════════════════════════════════════
# Sample 1: 标准 prototype 校准 (dissatisfaction domain)
# ═══════════════════════════════════════════════════════════════════════════
# 测试目标:
#   - handle_calibrate(prototype_texts_path=...) 分支
#   - 所有条件均有正反 prototype (standard member + non-member)
#   - process() 批处理路径
#   - 正反例明显区分
#
# 触发代码路径:
#   pyodide_handlers.py:handle_calibrate() lines 120-135
#   → TextCalibrationStage.process_with_outcome()
#   → _precompute_scores() → _fallback_text_scores() (无 BERT 时)
#   → DirectCalibration.calibrate() (基于变异的 raw scores)

SAMPLE1_CSV = """text_id,domain,text,expected_outcome
p1a,dissatisfaction,"你们这服务真的太差了，跑了好几趟都不给办，窗口人员态度恶劣还推诿扯皮，我非常愤怒要投诉到底",1
p1b,dissatisfaction,"去办证被刁难，材料齐全偏说缺这个缺那个，来回踢皮球，这已经不是第一次了",1
p1c,dissatisfaction,"为什么我们小区就不能办？别人都能办这是区别对待太不公平了我要找领导反映",1
p1d,dissatisfaction,"今天去问了一下补办流程，工作人员简单说了一下，虽然不是特别满意但也没办法",0
p1e,dissatisfaction,"请问一下这个业务现在还能办吗，需要带什么材料过去，大概多长时间能办好",0
p1f,dissatisfaction,"整体来说比上次好一点了，虽然还在等但起码有进展了，希望能尽快办完吧",0
"""

SAMPLE1_CONDITION_SET = {
    "name": "sample1_prototype_calibration",
    "description": "Sample 1: 标准 prototype 校准 — dissatisfaction domain, 所有条件均有正反 prototype",
    "domain": "dissatisfaction",
    "scoring_source": "prototype",
    "conditions": [
        {
            "name": "strong_negative_affect",
            "display_name": "强烈负面情感",
            "domain": "dissatisfaction",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否表达强烈负面情感",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "service_failure_mention",
            "display_name": "服务失败提及",
            "domain": "dissatisfaction",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否提及具体的服务失败经历",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "urgency_expression",
            "display_name": "急迫性表达",
            "domain": "dissatisfaction",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否表达急迫性",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "comparative_complaint",
            "display_name": "比较性投诉",
            "domain": "dissatisfaction",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否使用比较性不公平表达",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "escalation_threat",
            "display_name": "升级威胁",
            "domain": "dissatisfaction",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否威胁升级投诉",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
    ],
    "outcome": {
        "name": "high_dissatisfaction",
        "display_name": "高度不满",
        "domain": "dissatisfaction",
        "calibration_type": "direct",
        "calibration_params": {
            "threshold_full_in": 0.80,
            "threshold_full_out": 0.20,
            "crossover_point": 0.50,
            "direction": "ascending",
        },
        "description": "用户是否高度不满 (outcome)",
        "scoring_source": "prototype",
        "prototypes": [
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
}


# ═══════════════════════════════════════════════════════════════════════════
# Sample 2: 多条件混合校准（边缘 case） (trust domain)
# ═══════════════════════════════════════════════════════════════════════════
# 测试目标:
#   - 部分条件只有正例 prototype (无 is_member=0)
#     → CosineSimilarityEngine 的 positive-only edge case:
#       scores[:, j] = (sim_pos + 1.0) / 2.0
#   - 部分条件 weight != 1.0 (如 0.7, 0.5) → 测试加权 centroid
#   - 包含一个 outcome-only prototype 场景 (weight=0.3 弱信号)
#
# 触发代码路径:
#   cosine_similarity.py:compute_scores() lines 201-202
#   → centroid 聚合中 weights 影响归一化
#   → _fallback_text_scores() (无 BERT 时)

SAMPLE2_CSV = """text_id,domain,text,expected_outcome
p2a,trust,"我对政府非常信任，他们办事越来越透明，相信一定能公正处理好这件事，我要给他们点赞",1
p2b,trust,"工作人员非常专业，耐心解答我的所有问题，整个流程特别规范，很放心",1
p2c,trust,"政府真心为老百姓考虑，政策越来越贴心，虽然还有不足但一直在进步",1
p2d,trust,"我一点都不信任他们，说了半年了也没解决，政府部门就是互相推诿",0
p2e,trust,"办事人员很不专业，连基本政策都不清楚，问什么都不知道，太不靠谱了",0
p2f,trust,"这里面肯定有不公平的地方，有关系的人就优先，我们这种普通人就得排队等",0
"""

# Condition "competence_perception" 只有正例 prototype (测试 positive-only edge case)
# Condition "integrity_perception" weight=0.7 (测试加权 centroid)
# Outcome "high_trust" weight=0.3 (弱信号)
SAMPLE2_CONDITION_SET = {
    "name": "sample2_mixed_edge_cases",
    "description": "Sample 2: 多条件混合校准 — trust domain, positive-only + weighted prototypes",
    "domain": "trust",
    "scoring_source": "prototype",
    "conditions": [
        {
            "name": "institutional_trust",
            "display_name": "制度信任",
            "domain": "trust",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户对政府制度的普遍信任",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "competence_perception",
            "display_name": "能力感知",
            "domain": "trust",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户对政府能力的感知 — 仅正例 prototype (positive-only edge case)",
            "scoring_source": "prototype",
            # !! 只有正例: CosineSimilarityEngine → scores = (sim_pos + 1.0) / 2.0
            "prototypes": [
                {
                    "prototype_text": "工作人员非常专业能力强，办事效率高，解决得特别好很得力",
                    "is_member": 1,
                    "weight": 0.7,  # 非 1.0 weight — 测试加权 centroid
                },
            ],
        },
        {
            "name": "benevolence_perception",
            "display_name": "善意感知",
            "domain": "trust",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否认为政府有善意",
            "scoring_source": "prototype",
            "prototypes": [
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
        },
        {
            "name": "integrity_perception",
            "display_name": "公正感知",
            "domain": "trust",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否认为政府公正透明 (weight=0.7)",
            "scoring_source": "prototype",
            "prototypes": [
                {
                    "prototype_text": "工作人员按规定办事，公正透明，廉洁高效，全程公开",
                    "is_member": 1,
                    "weight": 0.7,  # 加权 centroid
                },
                {
                    "prototype_text": "这里面肯定有猫腻，不按规矩来，关系户优先",
                    "is_member": 0,
                    "weight": 0.5,  # 非对称 weight
                },
            ],
        },
        {
            "name": "positive_experience_share",
            "display_name": "正面体验分享",
            "domain": "trust",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测用户是否分享正面体验",
            "scoring_source": "prototype",
            "prototypes": [
                {
                    "prototype_text": "我要表扬他们，服务态度很好，值得点赞，非常满意，值得肯定",
                    "is_member": 1,
                    "weight": 0.6,  # 弱信号原型
                },
                {
                    "prototype_text": "服务太差了，我一点都不满意，必须给你们差评",
                    "is_member": 0,
                    "weight": 0.4,
                },
            ],
        },
    ],
    "outcome": {
        "name": "high_trust",
        "display_name": "高信任度",
        "domain": "trust",
        "calibration_type": "direct",
        "calibration_params": {
            "threshold_full_in": 0.80,
            "threshold_full_out": 0.20,
            "crossover_point": 0.50,
            "direction": "ascending",
        },
        "description": "用户是否对政府高度信任 (outcome, weight=0.3 弱信号)",
        "scoring_source": "prototype",
        # 弱信号 outcome: weight 仅 0.3
        "prototypes": [
            {
                "prototype_text": "我对政府很信任，办事很放心，相信他们会公正处理",
                "is_member": 1,
                "weight": 0.3,
            },
            {
                "prototype_text": "我对政府完全不信任，每次办事都不放心",
                "is_member": 0,
                "weight": 1.0,
            },
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# Sample 3: 嵌入校准 (embed-calibrate) (gov_responsiveness domain)
# ═══════════════════════════════════════════════════════════════════════════
# 测试目标:
#   - handle_embed_calibrate 路径 (前端传 embedding 给 Python)
#   - 条件包含 prototype_embeddings (虚拟 768-dim 向量)
#   - CosineSimilarityEngine.compute_scores 的完整路径
#   - handle_calibrate_prototype 的后向兼容 wrapper
#
# 触发代码路径:
#   pyodide_handlers.py:handle_embed_calibrate() lines 584-705
#   → _raw_conds 提取 prototype_embeddings (from raw dict)
#   → CosineSimilarityEngine.compute_scores()
#     → centroid aggregation + softmax scoring
#   → DirectCalibration.calibrate()
#
# 注意:
#   prototype_embeddings 不是 _condition_from_dict 反序列化的
#   (condition.py lines 200-221).
#   handle_embed_calibrate 从 raw JSON dict 中手动提取:
#     _raw_conds[_c["name"]] = _c → _raw.get("prototype_embeddings")
#   所以 prototype_embeddings 必须放在 condition dict 顶层键中.

# 辅助函数: 生成确定性的 768-dim 虚拟向量
import numpy as np  # noqa: E402 — 延迟导入用于说明

# 实际使用时 embedding 由 Transformers.js (前端) 或 ONNX 生成.
# 以下是 6 条文本 + 每个 condition 的 prototype 对应的 768-dim 虚拟向量.
# 使用常量 seed 确保可重现性.

DOMAIN = "gov_responsiveness"

# 条件名列表 (与下面 SAMPLE3_CONDITION_SET 中 conditions 的顺序一致)
SAMPLE3_CONDITION_NAMES = [
    "response_timeliness",
    "solution_effectiveness",
    "process_transparency",
    "interaction_quality",
    "follow_up_mechanism",
]

# Outcome 名
SAMPLE3_OUTCOME_NAME = "high_responsiveness"

# 6 条文本的 768-dim 虚拟向量 (随机种子 42, 确保可重现)
SAMPLE3_TEXT_EMBEDDINGS = None  # 将由 _generate_virtual_embeddings() 填充
SAMPLE3_PROTOTYPE_EMBEDDINGS = None  # 将由 _generate_virtual_embeddings() 填充


def _generate_virtual_embeddings():
    """生成 768-dim 虚拟向量用于测试目的.

    生成:
      - 6 条文本 x 768-dim (对应 SAMPLE3_CSV 的 6 条记录)
      - 每个 condition 每个 prototype x 768-dim

    使用确定性 seed (42) 确保可重现性.
    """
    rng = np.random.default_rng(42)

    # 文本向量 (6, 768)
    text_embs = rng.normal(loc=0.0, scale=0.1, size=(6, 768)).astype(np.float64)

    # 为每个 condition 的每个 prototype 生成向量
    # 正例 prototypes 与预期 positive-outcome 文本方向接近
    # 反例 prototypes 与预期 negative-outcome 文本方向不同
    proto_embs: dict[str, np.ndarray] = {}

    # outcome prototypes
    # 正例: 方向接近 p3a/p3b/p3c
    outcome_pos = rng.normal(loc=0.05, scale=0.1, size=(1, 768)).astype(np.float64)
    # 反例: 方向接近 p3d/p3e/p3f
    outcome_neg = rng.normal(loc=-0.05, scale=0.1, size=(1, 768)).astype(np.float64)
    proto_embs[SAMPLE3_OUTCOME_NAME] = np.vstack([outcome_pos, outcome_neg])

    for cond_name in SAMPLE3_CONDITION_NAMES:
        # 2 个 prototype (positive + negative)
        pos = rng.normal(loc=0.05, scale=0.1, size=(1, 768)).astype(np.float64)
        neg = rng.normal(loc=-0.05, scale=0.1, size=(1, 768)).astype(np.float64)
        proto_embs[cond_name] = np.vstack([pos, neg])

    return text_embs, proto_embs


SAMPLE3_TEXT_EMBEDDINGS, SAMPLE3_PROTOTYPE_EMBEDDINGS = _generate_virtual_embeddings()


SAMPLE3_CSV = """text_id,domain,text,expected_outcome
p3a,gov_responsiveness,"反映问题后当天就有人联系我了解情况，两天内就彻底解决了，效率非常高处理很到位",1
p3b,gov_responsiveness,"整个流程都有短信通知，每一步进展都告知我们，办完后还有回访电话询问满意度",1
p3c,gov_responsiveness,"工作人员态度非常好，非常耐心地解答了我的疑问，还主动帮我跟进后续办理情况",1
p3d,gov_responsiveness,"反映了好几次都没人理，打了好几个电话都说在核实，到现在一个月了也没回复",0
p3e,gov_responsiveness,"虽然有回复但一看就是敷衍，说什么正在处理中，实际上根本没有实际行动和进展",0
p3f,gov_responsiveness,"办完就没人管了，后续出了问题也不知道找谁，没有任何跟进回访机制",0
"""

# Condition definition 中包含 prototype_embeddings (768-dim 虚拟向量)
# 注意: prototype_embeddings 不是 _condition_from_dict() 消费的, handle_embed_calibrate()
# 从 raw dict 手动读取 _raw.get("prototype_embeddings").
SAMPLE3_CONDITION_SET = {
    "name": "sample3_embed_calibrate",
    "description": "Sample 3: 嵌入校准 — gov_responsiveness domain, 含虚拟 prototype_embeddings",
    "domain": "gov_responsiveness",
    "scoring_source": "prototype",
    "conditions": [
        {
            "name": "response_timeliness",
            "display_name": "响应及时性",
            "domain": "gov_responsiveness",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测政府是否及时响应",
            "scoring_source": "prototype",
            "prototypes": [
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
            # 2 x 768 — 行序对应 prototypes 数组
            "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
                "response_timeliness"
            ].tolist(),
        },
        {
            "name": "solution_effectiveness",
            "display_name": "解决有效性",
            "domain": "gov_responsiveness",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测问题是否得到有效解决",
            "scoring_source": "prototype",
            "prototypes": [
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
            "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
                "solution_effectiveness"
            ].tolist(),
        },
        {
            "name": "process_transparency",
            "display_name": "过程透明度",
            "domain": "gov_responsiveness",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测处理过程是否透明",
            "scoring_source": "prototype",
            "prototypes": [
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
            "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
                "process_transparency"
            ].tolist(),
        },
        {
            "name": "interaction_quality",
            "display_name": "互动质量",
            "domain": "gov_responsiveness",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测与服务人员的互动质量",
            "scoring_source": "prototype",
            "prototypes": [
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
            "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
                "interaction_quality"
            ].tolist(),
        },
        {
            "name": "follow_up_mechanism",
            "display_name": "后续跟进",
            "domain": "gov_responsiveness",
            "calibration_type": "direct",
            "calibration_params": {
                "threshold_full_in": 0.80,
                "threshold_full_out": 0.20,
                "crossover_point": 0.50,
                "direction": "ascending",
            },
            "description": "检测是否有后续跟进机制",
            "scoring_source": "prototype",
            "prototypes": [
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
            "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
                "follow_up_mechanism"
            ].tolist(),
        },
    ],
    "outcome": {
        "name": "high_responsiveness",
        "display_name": "高响应度",
        "domain": "gov_responsiveness",
        "calibration_type": "direct",
        "calibration_params": {
            "threshold_full_in": 0.80,
            "threshold_full_out": 0.20,
            "crossover_point": 0.50,
            "direction": "ascending",
        },
        "description": "政府是否高度响应 (outcome)",
        "scoring_source": "prototype",
        "prototypes": [
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
        "prototype_embeddings": SAMPLE3_PROTOTYPE_EMBEDDINGS[  # type: ignore[index]
            "high_responsiveness"
        ].tolist(),
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# 验证脚本 — 运行此文件验证所有 sample 结构正确
# ═══════════════════════════════════════════════════════════════════════════


def _validate_csv_structure(csv_text: str, label: str) -> None:
    """验证 CSV 字符串结构."""
    lines = [l.strip() for l in csv_text.strip().split("\n")]
    assert len(lines) >= 1, f"{label}: CSV 应有 header"
    header = lines[0]
    assert header == "text_id,domain,text,expected_outcome", (
        f"{label}: header 应为 'text_id,domain,text,expected_outcome', 实际为 {header!r}"
    )
    data_lines = lines[1:]
    assert len(data_lines) == 6, f"{label}: 应有 6 条数据, 实际 {len(data_lines)}"
    for i, line in enumerate(data_lines):
        # 基本格式校验: text_id,domain,"text...",0|1
        parts = line.split(",")
        assert len(parts) >= 4, f"{label} line {i + 1}: 字段数不足: {line!r}"
        # expected_outcome 必须是 0 或 1
        outcome_str = line.rstrip('"').split(",")[-1]
        assert outcome_str in ("0", "1"), (
            f"{label} line {i + 1}: expected_outcome 应为 0 或 1, 实际 {outcome_str!r}"
        )
    print(f"  [OK] {label}: CSV 结构有效 ({len(data_lines)} 条)")


def _validate_condition_set(data: dict, label: str) -> None:
    """验证 condition_set dict 结构."""
    assert "name" in data, f"{label}: 缺少 'name'"
    assert "description" in data, f"{label}: 缺少 'description'"
    assert "domain" in data, f"{label}: 缺少 'domain'"
    assert "scoring_source" in data, f"{label}: 缺少 'scoring_source'"
    assert "conditions" in data, f"{label}: 缺少 'conditions'"
    assert isinstance(data["conditions"], list), f"{label}: 'conditions' 应为 list"
    assert len(data["conditions"]) >= 1, f"{label}: conditions 不能为空"
    assert "outcome" in data, f"{label}: 缺少 'outcome'"
    assert data["outcome"] is not None, f"{label}: outcome 不能为 None"

    for i, cond in enumerate(data["conditions"]):
        assert "name" in cond, f"{label} condition[{i}]: 缺少 'name'"
        assert "prototypes" in cond, f"{label} condition[{i}]: 缺少 'prototypes'"
        assert isinstance(cond["prototypes"], list), (
            f"{label} condition[{i}]: 'prototypes' 应为 list"
        )
        for j, proto in enumerate(cond["prototypes"]):
            assert "prototype_text" in proto, (
                f"{label} condition[{i}] proto[{j}]: 缺少 'prototype_text'"
            )
            assert "is_member" in proto, (
                f"{label} condition[{i}] proto[{j}]: 缺少 'is_member'"
            )
            assert proto["is_member"] in (0, 1), (
                f"{label} condition[{i}] proto[{j}]: is_member 应为 0 或 1"
            )
            assert "weight" in proto, (
                f"{label} condition[{i}] proto[{j}]: 缺少 'weight'"
            )
            assert 0.0 <= proto["weight"] <= 1.0, (
                f"{label} condition[{i}] proto[{j}]: weight 应在 [0,1]"
            )

    outcome = data["outcome"]
    assert "prototypes" in outcome, f"{label} outcome: 缺少 'prototypes'"
    assert isinstance(outcome["prototypes"], list), (
        f"{label} outcome: 'prototypes' 应为 list"
    )

    print(f"  [OK] {label}: ConditionSet 结构有效 ({len(data['conditions'])} 个条件)")


def _validate_prototype_embeddings(data: dict, label: str) -> None:
    """验证 prototype_embeddings 结构 (Sample 3 专用)."""
    all_conds = list(data["conditions"])
    all_conds.append(data["outcome"])

    for i, cond in enumerate(all_conds):
        pe = cond.get("prototype_embeddings")
        if pe is not None:
            n_protos = len(cond["prototypes"])
            assert len(pe) == n_protos, (
                f"{label} cond[{i}] '{cond['name']}': "
                f"prototype_embeddings 行数 {len(pe)} != prototypes 数 {n_protos}"
            )
            for j, row in enumerate(pe):
                assert len(row) == 768, (
                    f"{label} cond[{i}] emb[{j}]: 维度应为 768, 实际 {len(row)}"
                )
            print(f"  [OK] {label}: prototype_embeddings 行数")


def _validate_text_embeddings(
    text_embs: np.ndarray | None, csv_text: str, label: str
) -> None:
    """验证文本 embedding 结构 (Sample 3 专用)."""
    if text_embs is None:
        return
    lines = csv_text.strip().split("\n")
    n_texts = len(lines) - 1  # 减去 header
    assert text_embs.shape == (n_texts, 768), (
        f"{label}: text_embeddings shape 应为 ({n_texts}, 768), 实际 {text_embs.shape}"
    )
    print(f"  [OK] {label}: text_embeddings shape = {text_embs.shape}")


def _check_text_variety(csv_text: str, label: str) -> None:
    """验证文本内容有足够变异 (避免 all-0.5 退化)."""
    lines = csv_text.strip().split("\n")[1:]  # 跳过 header
    texts = []
    for line in lines:
        # 提取引号中的文本
        start = line.index('"') + 1
        end = line.rindex('"')
        texts.append(line[start:end])

    lengths = [len(t) for t in texts]
    assert max(lengths) - min(lengths) > 5, (
        f"{label}: 文本长度差异太小 (min={min(lengths)}, max={max(lengths)}) "
        f"— 可能导致 min==max 退化"
    )

    # 检查文本内容不完全相同
    unique_texts = set(texts)
    assert len(unique_texts) == len(texts), f"{label}: 文本内容有重复 — 可能导致退化"
    print(f"  [OK] {label}: 文本长度变异充分 (range {min(lengths)}–{max(lengths)})")


def run_validation() -> None:
    """运行所有 3 组 sample 的结构验证."""
    print("=" * 60)
    print("Prototype Usage Samples — 结构验证")
    print("=" * 60)

    # ── Sample 1 ──────────────────────────────────────────────────────
    print("\n[Sample 1] 标准 prototype 校准 (dissatisfaction)")
    _validate_csv_structure(SAMPLE1_CSV, "Sample 1 CSV")
    _check_text_variety(SAMPLE1_CSV, "Sample 1")
    _validate_condition_set(SAMPLE1_CONDITION_SET, "Sample 1")

    # ── Sample 2 ──────────────────────────────────────────────────────
    print("\n[Sample 2] 多条件混合校准 (trust, positive-only + weighted)")
    _validate_csv_structure(SAMPLE2_CSV, "Sample 2 CSV")
    _check_text_variety(SAMPLE2_CSV, "Sample 2")
    _validate_condition_set(SAMPLE2_CONDITION_SET, "Sample 2")

    # 验证 positive-only edge case
    comp_cond = SAMPLE2_CONDITION_SET["conditions"][1]
    assert comp_cond["name"] == "competence_perception"
    has_neg = any(p["is_member"] == 0 for p in comp_cond["prototypes"])
    assert not has_neg, (
        "Sample 2: competence_perception 不应有 is_member=0 (positive-only test)"
    )
    print("  [OK] Sample 2: competence_perception 为 positive-only (测试 edge case)")

    # 验证非 1.0 weight
    integ_cond = SAMPLE2_CONDITION_SET["conditions"][3]
    assert integ_cond["name"] == "integrity_perception"
    weights = [p["weight"] for p in integ_cond["prototypes"]]
    assert any(w != 1.0 for w in weights), (
        "Sample 2: integrity_perception 应有非 1.0 weight"
    )
    print("  [OK] Sample 2: integrity_perception 有非对称 weights (测试加权 centroid)")

    pos_exp_cond = SAMPLE2_CONDITION_SET["conditions"][4]
    assert pos_exp_cond["name"] == "positive_experience_share"
    weights_pe = [p["weight"] for p in pos_exp_cond["prototypes"]]
    assert any(w != 1.0 for w in weights_pe), (
        "Sample 2: positive_experience_share 应有非 1.0 weight"
    )
    print("  [OK] Sample 2: positive_experience_share 有非 1.0 weight")

    # 验证 outcome weight=0.3 弱信号
    outcome = SAMPLE2_CONDITION_SET["outcome"]
    assert outcome["name"] == "high_trust"
    outcome_weights = [p["weight"] for p in outcome["prototypes"]]
    assert 0.3 in outcome_weights, "Sample 2: outcome 应有 weight=0.3"
    print("  [OK] Sample 2: outcome 含 weight=0.3 弱信号")

    # ── Sample 3 ──────────────────────────────────────────────────────
    print("\n[Sample 3] 嵌入校准 (gov_responsiveness, 虚拟 768-dim)")
    _validate_csv_structure(SAMPLE3_CSV, "Sample 3 CSV")
    _check_text_variety(SAMPLE3_CSV, "Sample 3")
    _validate_condition_set(SAMPLE3_CONDITION_SET, "Sample 3")
    _validate_prototype_embeddings(SAMPLE3_CONDITION_SET, "Sample 3")
    _validate_text_embeddings(SAMPLE3_TEXT_EMBEDDINGS, SAMPLE3_CSV, "Sample 3")

    print("\n" + "=" * 60)
    print("All 3 samples validated successfully!")
    print("=" * 60)

    # ── 测试用脚本示例 ──────────────────────────────────────────────
    print("\n── 使用示例 ──")
    print("""
# Sample 1: handle_calibrate (prototype_texts_path 分支)
# 将 CSV 文本作为 prototype texts, 通过 handle_calibrate 的 prototypeTexts
# 参数传入, 使用 process() 批处理校准.
#
#   Frontend (DataInput.tsx):
#     const { fuzzyData, prototypeFuzzyData } = await handleCalibrate(
#       textCorpusEntries,
#       conditionSet,
#       { prototypeTexts: parsedTextCases }  // ← SAMPLE1_CSV 解析后的 TextCase[]
#     );
#
#   Python 侧:
#     handle_calibrate(
#       texts_path="/tmp/raw_texts.json",
#       condition_set_path="/tmp/condition_set.json",
#       output_path="/tmp/output.json",
#       prototype_texts_path="/tmp/prototype_texts.json",  // ← 此为 SAMPLE1_CSV 数据
#     )

# Sample 2: 边缘 case 测试
# competence_perception 只有正例 prototype (is_member=1)
# → CosineSimilarityEngine.compute_scores() 走 positive-only branch:
#   scores[:, j] = (sim_pos + 1.0) / 2.0
# integrity_perception weight=0.7/0.5 → 测试加权 centroid
# outcome high_trust weight=0.3 → 弱信号 outcome
#
#   Frontend:
#     与 Sample 1 相同的 handle_calibrate 调用路径,
#     但 conditionSet 使用 SAMPLE2_CONDITION_SET
#
#   确保先用 yamlToConditionSet() 解析:
#     const parsed = yamlToConditionSet(yamlString);
#     const conditionSet = ensureQCAVariant(parsed, qcaVariant);

# Sample 3: embed-calibrate
# 前端用 Transformers.js 计算 BERT embedding, 传 768-dim 向量给 Python
# → handle_embed_calibrate() → CosineSimilarityEngine.compute_scores()
#   → centroid + softmax scoring
# handle_calibrate_prototype 作为后向兼容 wrapper 也可用
#
#   Frontend:
#     const textsWithEmbeddings = textCorpusEntries.map((entry, i) => ({
#       text_id: entry.text_id,
#       text: entry.text,
#       embedding: textEmbeddings[i],  // 768-dim float array from BertEngine
#     }));
#     const fuzzyData = await handleEmbedCalibrate(
#       textsWithEmbeddings,
#       conditionSet
#     );
""")


if __name__ == "__main__":
    run_validation()
