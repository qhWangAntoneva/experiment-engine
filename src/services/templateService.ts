/**
 * Condition Set Sharing & Team Templates (P1-13)
 *
 * Provides:
 *   - Share link encoding/decoding via base64url
 *   - Built-in domain templates (hardcoded from domains.py)
 *   - Imported template persistence in localStorage
 */

import type {
  ConditionSet,
  ConditionDefinition,
  ConditionSetTemplate,
  ConceptPrototype,
  CalibrationMethod,
  TextDomain,
} from '../types/qca';
import { CalibrationMethod as CM } from '../types/qca';

// ─── Constants ────────────────────────────────────────────────────────────────

const SHARE_VERSION = 1;
const TEMPLATES_KEY = 'qca-templates';

// ─── Shareable Payload ─────────────────────────────────────────────────────────

interface ShareableConditionSet {
  v: number;
  name: string;
  description: string;
  domain: TextDomain;
  conditions: ShareableCondition[];
  outcome: ShareableCondition | null;
}

interface ShareableCondition {
  name: string;
  display_name: string;
  domain: TextDomain;
  calibration_type: string;
  calibration_params: {
    threshold_full_in: number;
    threshold_full_out: number;
    crossover_point: number;
    direction: 'ascending' | 'descending';
    steepness?: number;
  } | null;
  description: string;
  prototypes: Array<{
    prototype_text: string;
    is_member: 0 | 1;
    weight: number;
  }>;
}

// ─── ConditionSet <-> ShareableConditionSet ────────────────────────────────────

function conditionSetToShareable(cs: ConditionSet): ShareableConditionSet {
  const toShareable = (c: ConditionDefinition): ShareableCondition => ({
    name: c.name,
    display_name: c.display_name,
    domain: c.domain,
    calibration_type: c.calibration_type,
    calibration_params: c.calibration_params,
    description: c.description,
    prototypes: (c.prototypes ?? []).map((p) => ({
      prototype_text: p.prototype_text,
      is_member: p.is_member,
      weight: p.weight,
    })),
  });

  return {
    v: SHARE_VERSION,
    name: cs.name,
    description: cs.description,
    domain: cs.domain,
    conditions: cs.conditions.map(toShareable),
    outcome: cs.outcome ? toShareable(cs.outcome) : null,
  };
}

function shareableToConditionSet(payload: ShareableConditionSet): ConditionSet {
  const toCondition = (c: ShareableCondition): ConditionDefinition => ({
    name: c.name,
    display_name: c.display_name,
    domain: c.domain,
    calibration_type: c.calibration_type as CalibrationMethod,
    calibration_params: c.calibration_params,
    description: c.description,
    scoring_source: 'prototype',
    prototypes: (c.prototypes ?? []).map(
      (p): ConceptPrototype => ({
        prototype_text: p.prototype_text,
        is_member: p.is_member,
        weight: p.weight,
      })
    ),
    prototype_embeddings: null,
    embedding_model: null,
  });

  return {
    name: payload.name,
    description: payload.description,
    domain: payload.domain,
    conditions: payload.conditions.map(toCondition),
    outcome: payload.outcome ? toCondition(payload.outcome) : null,
    scoring_source: 'prototype',
  };
}

// ─── Encode / Decode ───────────────────────────────────────────────────────────

function base64urlEncode(str: string): string {
  return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64urlDecode(str: string): string {
  let s = str.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return atob(s);
}

/**
 * Strip prototype_embeddings and encode a ConditionSet as a base64url share payload.
 */
export function encodeConditionSetForShare(cs: ConditionSet): string {
  const shareable = conditionSetToShareable(cs);
  const json = JSON.stringify(shareable);
  return base64urlEncode(json);
}

/**
 * Validate and decode a base64url share payload back into a ConditionSet.
 * Returns null if validation fails.
 */
export function decodeSharedConditionSet(payload: string): ConditionSet | null {
  try {
    const json = base64urlDecode(payload);
    const obj = JSON.parse(json) as ShareableConditionSet;

    // Validate
    if (obj.v !== SHARE_VERSION) return null;
    if (!obj.name || typeof obj.name !== 'string') return null;
    if (!Array.isArray(obj.conditions) || obj.conditions.length === 0) return null;
    if (!obj.domain || typeof obj.domain !== 'string') return null;

    // Validate each condition has required fields
    for (const c of obj.conditions) {
      if (!c.name || !c.display_name || !c.domain || !c.calibration_type) return null;
      if (!Array.isArray(c.prototypes) || c.prototypes.length === 0) return null;
    }

    return shareableToConditionSet(obj);
  } catch {
    return null;
  }
}

/**
 * Generate a full share URL with ?share= parameter for the current origin.
 */
export function generateShareUrl(cs: ConditionSet): string {
  const payload = encodeConditionSetForShare(cs);
  const origin = window.location.origin;
  const path = window.location.pathname;
  // Build the URL to the dashboard (the share import modal lives there)
  const baseUrl = `${origin}${path}`;
  // Remove any existing hash/params, use root for SPA
  const rootUrl = origin;
  return `${rootUrl}/?share=${payload}`;
}

// ─── Built-in Domain Templates ─────────────────────────────────────────────────

const DEFAULT_CALIBRATION = {
  threshold_full_in: 0.80,
  threshold_full_out: 0.20,
  crossover_point: 0.50,
  direction: 'ascending' as const,
};

function makeBuiltinTemplate(
  id: string,
  name: string,
  description: string,
  domain: TextDomain,
  conditions: Array<{ name: string; display: string; desc: string; prototypes: Array<{ text: string; isMember: 0 | 1 }> }>,
  outcome: { name: string; display: string; desc: string; prototypes: Array<{ text: string; isMember: 0 | 1 }> }
): ConditionSetTemplate {
  const toConditionDef = (
    cname: string,
    display: string,
    desc: string,
    prototypes: Array<{ text: string; isMember: 0 | 1 }>
  ): ConditionDefinition => ({
    name: cname,
    display_name: display,
    domain,
    calibration_type: CM.DIRECT,
    calibration_params: DEFAULT_CALIBRATION,
    description: desc,
    scoring_source: 'prototype',
    prototypes: prototypes.map(
      (p): ConceptPrototype => ({
        prototype_text: p.text,
        is_member: p.isMember,
        weight: 1.0,
      })
    ),
    prototype_embeddings: null,
    embedding_model: null,
  });

  const condDefs = conditions.map((c) => toConditionDef(c.name, c.display, c.desc, c.prototypes));
  const outcomeDef = toConditionDef(outcome.name, outcome.display, outcome.desc, outcome.prototypes);

  return {
    id,
    name,
    description,
    domain,
    conditions: condDefs,
    outcome: outcomeDef,
    conditionCount: condDefs.length,
    source: 'builtin',
    createdAt: '2025-01-01T00:00:00Z',
  };
}

/**
 * Return all 5 built-in domain templates hardcoded from domains.py DOMAIN_PRESETS.
 */
export function getBuiltinTemplates(): ConditionSetTemplate[] {
  return [
    makeBuiltinTemplate(
      'builtin-dissatisfaction',
      'Dissatisfaction',
      'Citizen dissatisfaction analysis: negative affect, service failure, urgency, comparative complaint, escalation threat',
      'dissatisfaction',
      [
        {
          name: 'strong_negative_affect',
          display: 'Strong Negative Affect',
          desc: 'Intense negative emotional expression (anger, frustration, disappointment)',
          prototypes: [
            { text: '你们这服务太差了，态度恶劣，办事效率极低，我非常愤怒要投诉你们', isMember: 1 },
            { text: '请帮我查一下这个申请什么时候能办好，谢谢', isMember: 0 },
          ],
        },
        {
          name: 'service_failure_mention',
          display: 'Service Failure Mention',
          desc: 'Reports of procedural failures, delays, or bureaucratic obstruction',
          prototypes: [
            { text: '我去办证跑了好几趟都没办成，窗口人员互相推诿踢皮球，不予办理', isMember: 1 },
            { text: '工作人员态度很好，耐心解答了我的问题，顺利办完了', isMember: 0 },
          ],
        },
        {
          name: 'urgency_expression',
          display: 'Urgency Expression',
          desc: 'Expressions of time pressure, critical need for immediate resolution',
          prototypes: [
            { text: '这个问题急需解决，迫在眉睫，不能再等了，耽误不起，请立即处理', isMember: 1 },
            { text: '慢慢来吧，等你们有空了再帮我处理一下就行', isMember: 0 },
          ],
        },
        {
          name: 'comparative_complaint',
          display: 'Comparative Complaint',
          desc: 'Comparison with other jurisdictions or perceived unequal treatment',
          prototypes: [
            { text: '为什么别的地方能办我们这里就不行？凭什么区别对待，太不公平了', isMember: 1 },
            { text: '我想了解一下这个业务的办理流程是什么', isMember: 0 },
          ],
        },
        {
          name: 'escalation_threat',
          display: 'Escalation Threat',
          desc: 'Threats to escalate complaint to higher authorities, media, or legal action',
          prototypes: [
            { text: '如果再不解决我就打市长热线，找纪委和媒体曝光你们', isMember: 1 },
            { text: '希望能尽快帮我处理一下，我已经等了一周了', isMember: 0 },
          ],
        },
      ],
      {
        name: 'high_dissatisfaction',
        display: 'High Dissatisfaction',
        desc: 'Overall high dissatisfaction and negative evaluation of service',
        prototypes: [
          { text: '你们的服务太差了，严重不作为，我对你们彻底失望', isMember: 1 },
          { text: '事情办完了，效率还可以，整体来说比较满意', isMember: 0 },
        ],
      }
    ),
    makeBuiltinTemplate(
      'builtin-policy_demand',
      'Policy Demand',
      'Citizen policy demand analysis: specific proposals, resource requests, group representation, evidence citation, feasibility arguments',
      'policy_demand',
      [
        {
          name: 'specific_policy_proposal',
          display: 'Specific Policy Proposal',
          desc: 'Concrete policy suggestions, regulatory changes, or institutional reforms',
          prototypes: [
            { text: '建议政府制定相关惠民政策，完善城市管理制度，修改不合理的旧规定', isMember: 1 },
            { text: '我就想问一下现在这个政策具体是怎么执行的', isMember: 0 },
          ],
        },
        {
          name: 'resource_request',
          display: 'Resource Request',
          desc: 'Requests for funding, subsidies, or material resource allocation',
          prototypes: [
            { text: '我们需要政府增加资金投入和财政支持，给老百姓发放更多补贴', isMember: 1 },
            { text: '这个政策很好，希望能够尽快落实到位', isMember: 0 },
          ],
        },
        {
          name: 'group_representation',
          display: 'Group Representation',
          desc: 'Claims to represent collective interests beyond individual concerns',
          prototypes: [
            { text: '我们全体居民代表大家反映这个问题，这是广大群众的共同心声', isMember: 1 },
            { text: '我个人觉得这个政策对我们家影响挺大的', isMember: 0 },
          ],
        },
        {
          name: 'evidence_citation',
          display: 'Evidence Citation',
          desc: 'References to data, research, or successful precedents from other jurisdictions',
          prototypes: [
            { text: '据统计数据显示，研究表明这种做法在其他城市已有成功先例可以参考', isMember: 1 },
            { text: '我觉得这个做法应该能行，大家都会支持的', isMember: 0 },
          ],
        },
        {
          name: 'feasibility_argument',
          display: 'Feasibility Argument',
          desc: 'Arguments that the proposed policy is practical and achievable',
          prototypes: [
            { text: '这个方案是可以做到的，其他城市已有先例，条件完全具备，难度不大', isMember: 1 },
            { text: '这个事情太难了，我觉得根本不可能实现', isMember: 0 },
          ],
        },
      ],
      {
        name: 'strong_policy_demand',
        display: 'Strong Policy Demand',
        desc: 'Overall strong expression of policy need and demand for government action',
        prototypes: [
          { text: '我们强烈要求政府尽快出台相关政策，迫切需要解决这个问题', isMember: 1 },
          { text: '随便了解一下这个政策的具体内容是什么', isMember: 0 },
        ],
      }
    ),
    makeBuiltinTemplate(
      'builtin-co_production',
      'Co-Production',
      'Citizen co-production analysis: willingness to participate, resource contributions, knowledge sharing, collective action calls',
      'co_production',
      [
        {
          name: 'willingness_to_participate',
          display: 'Willingness to Participate',
          desc: 'Expressions of willingness to engage in governance or community activities',
          prototypes: [
            { text: '我愿意积极参加社区治理工作，配合你们一起把这件事做好', isMember: 1 },
            { text: '这是政府该管的事，跟我们普通老百姓没什么关系', isMember: 0 },
          ],
        },
        {
          name: 'resource_contribution_offer',
          display: 'Resource Contribution Offer',
          desc: 'Offers to provide funding, materials, or other resources',
          prototypes: [
            { text: '我们愿意出资出力，捐赠物资，提供必要资源来共同解决这个问题', isMember: 1 },
            { text: '你们政府自己想办法解决，我们没钱也没资源', isMember: 0 },
          ],
        },
        {
          name: 'knowledge_sharing',
          display: 'Knowledge Sharing',
          desc: 'Offers to share expertise, technical knowledge, or professional advice',
          prototypes: [
            { text: '据我了解和我多年经验，我从专业角度提几点技术建议和信息共享', isMember: 1 },
            { text: '我不太懂这些，你们专业人士看着办就行', isMember: 0 },
          ],
        },
        {
          name: 'collective_action_call',
          display: 'Collective Action Call',
          desc: 'Calls for organizing collective action and coordinated efforts',
          prototypes: [
            { text: '大家一起齐心协力，组织起来联合行动，共同把这事办好', isMember: 1 },
            { text: '我一个人来反映一下意见就行了，不需要别人一起', isMember: 0 },
          ],
        },
      ],
      {
        name: 'co_production_request',
        display: 'Co-Production Request',
        desc: 'Overall expression of desire for collaborative governance and co-production',
        prototypes: [
          { text: '我们希望与政府合作共建，协同推动社区参与治理', isMember: 1 },
          { text: '请帮我查询一下这个文件的具体办理进度', isMember: 0 },
        ],
      }
    ),
    makeBuiltinTemplate(
      'builtin-trust',
      'Trust',
      'Citizen trust analysis: institutional trust, competence perception, benevolence perception, integrity perception, positive experiences',
      'trust',
      [
        {
          name: 'institutional_trust',
          display: 'Institutional Trust',
          desc: 'Trust in government institutions, reliability, and credibility',
          prototypes: [
            { text: '我相信政府一定能把这件事处理好，政府办事越来越可靠值得信赖', isMember: 1 },
            { text: '政府没什么公信力，我不相信他们能解决好这个问题', isMember: 0 },
          ],
        },
        {
          name: 'competence_perception',
          display: 'Competence Perception',
          desc: 'Perception of government staff professionalism and efficiency',
          prototypes: [
            { text: '工作人员非常专业能力强，办事效率高，解决得特别好很得力', isMember: 1 },
            { text: '办事人员不专业，连基本政策都解释不清楚', isMember: 0 },
          ],
        },
        {
          name: 'benevolence_perception',
          display: 'Benevolence Perception',
          desc: 'Perception that government genuinely cares about citizen welfare',
          prototypes: [
            { text: '政府真心为老百姓着想，关心群众生活，政策很贴心很人性化', isMember: 1 },
            { text: '政府根本不关心我们的实际困难，只顾自己方便', isMember: 0 },
          ],
        },
        {
          name: 'integrity_perception',
          display: 'Integrity Perception',
          desc: 'Perception of fairness, transparency, and procedural justice',
          prototypes: [
            { text: '工作人员按规定办事，公正透明，廉洁高效，全程公开', isMember: 1 },
            { text: '这里面肯定有猫腻，不按规矩来，关系户优先', isMember: 0 },
          ],
        },
        {
          name: 'positive_experience_share',
          display: 'Positive Experience Share',
          desc: 'Sharing of positive service experiences and satisfaction',
          prototypes: [
            { text: '我要表扬他们，服务态度很好，值得点赞，非常满意，值得肯定', isMember: 1 },
            { text: '服务太差了，我一点都不满意，必须给你们差评', isMember: 0 },
          ],
        },
      ],
      {
        name: 'high_trust',
        display: 'High Trust',
        desc: 'Overall high trust and confidence in government',
        prototypes: [
          { text: '我对政府很信任，办事很放心，相信他们会公正处理', isMember: 1 },
          { text: '我对政府完全不信任，每次办事都不放心', isMember: 0 },
        ],
      }
    ),
    makeBuiltinTemplate(
      'builtin-gov_responsiveness',
      'Government Responsiveness',
      'Government responsiveness analysis: response timeliness, solution effectiveness, process transparency, interaction quality, follow-up mechanisms',
      'gov_responsiveness',
      [
        {
          name: 'response_timeliness',
          display: 'Response Timeliness',
          desc: 'Speed and timeliness of government response to citizen inquiries',
          prototypes: [
            { text: '当天就回复了，处理速度很快，三个工作日内就全部办完了', isMember: 1 },
            { text: '等了好几天也没个回复，到现在都不知道进展怎么样了', isMember: 0 },
          ],
        },
        {
          name: 'solution_effectiveness',
          display: 'Solution Effectiveness',
          desc: 'Whether problems were actually solved, and how thoroughly',
          prototypes: [
            { text: '问题已经解决了，办好了，处理非常到位，落实得很好很彻底', isMember: 1 },
            { text: '虽然回复了但是问题根本没解决，敷衍了事', isMember: 0 },
          ],
        },
        {
          name: 'process_transparency',
          display: 'Process Transparency',
          desc: 'Transparency of procedures, information disclosure, and status feedback',
          prototypes: [
            { text: '整个过程都公开公示了，每一步都告知我们，解释得很清楚有结果反馈', isMember: 1 },
            { text: '什么信息都不公开，问了好几次也不告诉我们进展', isMember: 0 },
          ],
        },
        {
          name: 'interaction_quality',
          display: 'Interaction Quality',
          desc: 'Quality of staff-citizen interaction: attitude, patience, attentiveness',
          prototypes: [
            { text: '工作人员态度好很有耐心，认真细致，热情周到，服务非常贴心', isMember: 1 },
            { text: '工作人员态度冷漠，问三句答一句，一副不耐烦的样子', isMember: 0 },
          ],
        },
        {
          name: 'follow_up_mechanism',
          display: 'Follow-Up Mechanism',
          desc: 'Presence of post-resolution follow-up, continued attention, and feedback loops',
          prototypes: [
            { text: '办理后还有回访电话，后续跟进做得很到位，持续关注我们的情况', isMember: 1 },
            { text: '办完就完了，没有任何后续跟进，出了问题也不知道找谁', isMember: 0 },
          ],
        },
      ],
      {
        name: 'high_responsiveness',
        display: 'High Responsiveness',
        desc: 'Overall high government responsiveness and citizen satisfaction with response',
        prototypes: [
          { text: '政府非常负责，响应非常及时，处理效率很高，我们很满意', isMember: 1 },
          { text: '投诉了也没用，根本没人管，效率太低了', isMember: 0 },
        ],
      }
    ),
  ];
}

// ─── Imported Templates (localStorage) ──────────────────────────────────────────

export function getImportedTemplates(): ConditionSetTemplate[] {
  try {
    const raw = localStorage.getItem(TEMPLATES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as ConditionSetTemplate[];
  } catch {
    return [];
  }
}

export function saveImportedTemplate(template: ConditionSetTemplate): void {
  try {
    const existing = getImportedTemplates();
    // Avoid duplicates by id
    const idx = existing.findIndex((t) => t.id === template.id);
    if (idx >= 0) {
      existing[idx] = template;
    } else {
      existing.unshift(template);
    }
    localStorage.setItem(TEMPLATES_KEY, JSON.stringify(existing));
  } catch {
    // localStorage full or unavailable
  }
}

export function removeImportedTemplate(id: string): void {
  try {
    const existing = getImportedTemplates();
    const filtered = existing.filter((t) => t.id !== id);
    localStorage.setItem(TEMPLATES_KEY, JSON.stringify(filtered));
  } catch {
    // ignore
  }
}
