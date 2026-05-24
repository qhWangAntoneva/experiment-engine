# 贡献指南

欢迎贡献 experiment-engine！本文档帮助您快速上手开发、提交规范的 PR，并与团队保持一致的代码风格。

> **项目版本**：0.1.0 · Python ≥3.10 · [GitHub](https://github.com/qhWangAntoneva/experiment-engine)

---

## 1. 开发环境搭建

### 1.1 克隆仓库

```bash
git clone https://github.com/qhWangAntoneva/experiment-engine.git
cd experiment-engine
```

### 1.2 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 1.3 安装开发依赖

使用可编辑安装 + `dev` 可选依赖：

```bash
pip install -e ".[dev]"
```

`dev` 依赖包含：pytest、ruff、mypy、pre-commit 等。如需要 API 文档工具，额外安装：

```bash
pip install -e ".[docs]"
```

### 1.4 验证安装

```bash
python -m experiment_engine --version
# 输出：experiment-engine, version 0.1.0
```

---

## 2. 代码风格

项目使用 [ruff](https://docs.astral.sh/ruff/) 完成 lint 与 format，配置位于 `pyproject.toml`。

### 2.1 代码检查

```bash
ruff check src/ tests/
```

启用的规则集：`E`, `F`, `I`, `N`, `W`, `UP`, `B`, `SIM`, `ARG`, `PD`, `RUF`, `C4`, `T20`, `RET`, `SLF`。

忽略规则：`B008`（允许函数参数默认值为可变类型）、`ARG001`/`ARG002`（允许未使用的函数参数）。

### 2.2 自动格式化

```bash
ruff format src/ tests/
```

格式规范：
- 双引号字符串（`pyproject.toml` 中 `quote-style = "double"`）
- 空格缩进，每行 88 字符（ruff 默认值）
- 兼容 Python 3.10+

### 2.3 一行命令同时 lint + format

```bash
ruff check src/ tests/ --fix && ruff format src/ tests/
```

---

## 3. 类型检查

项目使用 [mypy](https://mypy-lang.org/) 进行静态类型检查，配置级别为 **report-only**（不阻塞 CI）：

```bash
mypy src/
```

配置要点（`pyproject.toml`）：
- `warn_return_any = true` — 对返回 `Any` 的函数发出警告
- `strict_optional = true` — 严格处理 `Optional` 类型
- `no_implicit_reexport = true` — 模块必须显式 re-export
- `strict_equality = true` — 禁止不同类型之间的 `==`/`!=`
- `ignore_missing_imports = true` — 忽略第三方库缺少类型 stub

> 建议：新增公共 API 时尽量提供完整的类型注解。mypy 的 warning 应尽量消除，但不作为 PR 合并的硬性门槛。

---

## 4. 测试要求

项目使用 [pytest](https://docs.pytest.org/)，配置文件位于 `pyproject.toml` 的 `[tool.pytest.ini_options]`。

### 4.1 运行测试

```bash
# 运行全部测试
pytest

# 带覆盖率报告
pytest --cov=src/experiment_engine --cov-report=term-missing

# 运行指定测试文件
pytest tests/test_pipeline.py

# 运行指定测试函数
pytest tests/test_pipeline.py::test_pipeline_run

# 显示详细输出
pytest -v

# 仅运行失败的测试
pytest --lf
```

### 4.2 测试规范

| 要求 | 说明 |
|------|------|
| **测试文件命名** | `test_*.py`，放在 `tests/` 目录下 |
| **测试函数命名** | `test_*` 前缀 |
| **新增功能** | 必须附带对应的单元测试 |
| **Bug 修复** | 建议先添加复现该 bug 的测试用例 |
| **测试隔离** | 每个测试独立，不依赖执行顺序 |
| **Mock 外部依赖** | 文件 I/O、网络请求等应使用 `monkeypatch` 或 `unittest.mock` |

### 4.3 测试覆盖率

目前项目有 **295 个通过测试，6 个预期失败（xfail）**。新增功能应尽量保持或提升行覆盖率（`--cov-report=term-missing` 可查看未覆盖的行）。

### 4.4 测试目录结构

```
tests/
├── conftest.py          # 共享 fixtures
├── test_pipeline.py     # Pipeline 核心逻辑
├── test_io.py           # I/O 模块
├── test_viz.py          # 可视化模块
├── test_integration.py  # 集成测试
└── ...                   # 其他模块测试
```

---

## 5. Pre-commit 钩子

项目配置了 [pre-commit](https://pre-commit.com/) 来在提交前自动检查代码质量。

### 5.1 安装钩子

```bash
pre-commit install
```

安装后，每次 `git commit` 会自动运行配置的钩子。如果钩子失败，提交会被阻止。

### 5.2 手动运行

```bash
# 对所有文件运行
pre-commit run --all-files

# 对暂存区文件运行
pre-commit run
```

### 5.3 配置的钩子列表（`.pre-commit-config.yaml`）

| 钩子 | 作用 |
|------|------|
| `trailing-whitespace` | 去除行尾空格 |
| `end-of-file-fixer` | 确保文件末尾有且只有一个换行 |
| `check-yaml` | 校验 YAML 文件语法 |
| `check-toml` | 校验 TOML 文件语法 |
| `check-json` | 校验 JSON 文件语法 |
| `check-added-large-files` | 阻止添加大文件（默认 >500KB） |
| `ruff` (with `--fix`) | 自动修复 lint 问题 |
| `ruff-format` | 自动格式化代码 |

> 注意：建议在提交前先手动运行 `ruff check --fix && ruff format`，以加快 pre-commit 执行速度。

---

## 6. PR 流程

项目使用 GitHub Flow（无 GitHub CLI 时的本地开发流程）。

### 6.1 本地开发流程

```bash
# 1. 确保在 main 分支且是最新
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feat/my-feature      # 新功能
# 或
git checkout -b fix/my-bugfix        # Bug 修复
# 或
git checkout -b docs/my-doc-update   # 文档变更

# 3. 开发 & 提交
# ... 修改代码 ...
git add <files>
git commit -m "feat: 简洁的描述（< 50 字符）"

# 4. 同步远程变更（避免冲突）
git fetch origin
git rebase origin/main

# 5. 运行本地检查清单
ruff check src/ tests/ --fix && ruff format src/ tests/   # 代码风格
mypy src/                                                  # 类型检查（可选）
pytest                                                     # 全部测试通过
pre-commit run --all-files                                 # pre-commit 检查

# 6. 推送分支
git push origin feat/my-feature
```

### 6.2 创建 Pull Request

1. 在 GitHub 仓库页面点击 **New Pull Request**
2. base 选择 `main`，compare 选择您的分支
3. PR 标题遵循 [Conventional Commits](https://www.conventionalcommits.org/) 格式：
   - `feat:` — 新功能
   - `fix:` — Bug 修复
   - `refactor:` — 重构
   - `docs:` — 文档变更
   - `test:` — 测试相关
   - `chore:` — 构建/工具变更
4. PR 描述包含：
   - **变更摘要** — 做了什么、为什么
   - **关联 Issue**（如果有）— `Closes #123`
   - **检查清单** — 确认已运行测试、lint、pre-commit

### 6.3 分支命名规范

```
feat/<简短描述>
fix/<简短描述>
docs/<简短描述>
refactor/<简短描述>
test/<简短描述>
chore/<简短描述>
```

---

## 7. 代码审查指南

### 7.1 审查重点

审查者应关注以下方面：

| 维度 | 检查要点 |
|------|----------|
| **正确性** | 逻辑是否正确？边界情况是否处理？现有测试是否通过？ |
| **类型安全** | 新增的公共 API 是否有完整类型注解？mypy 是否无新增 warning？ |
| **测试覆盖** | 新增功能是否有测试？测试是否覆盖了正常路径和异常路径？ |
| **代码风格** | 是否符合 ruff 规范？命名是否清晰？代码是否易于理解？ |
| **架构一致性** | 代码是否符合现有模块分层？是否合理使用了 Pydantic 模型？ |
| **文档** | 公共 API 是否有 docstring？复杂逻辑是否有注释？ |

### 7.2 审查流程

1. 审查者在 PR 上添加行级评论
2. 贡献者根据反馈修改代码并推送新 commit
3. 重复直至所有讨论 resolved
4. 至少 **1 名维护者 Approve** 后方可合并
5. 合并方式：**Squash and merge**（保持 main 分支历史清晰）

### 7.3 审查礼仪

- **对事不对人** — 关注代码本身，而非作者
- **解释理由** — 给出具体的改进建议和原因
- **区分主次** — 用「建议」「nit」「blocking」标注评论的优先级
- **及时响应** — 审查者和贡献者都应尽量在 48 小时内回复

---

## 附录：项目结构速览

```
experiment-engine/
├── src/
│   └── experiment_engine/
│       ├── __init__.py       # 公共 API 导出（Pipeline, Stage, PluginRegistry 等）
│       ├── __main__.py       # python -m 入口
│       ├── cli.py            # Click CLI（run, validate, list-plugins）
│       ├── models.py         # Pydantic 数据模型
│       ├── pipeline.py       # Pipeline + Stage ABC
│       ├── config.py         # 配置加载与合并
│       ├── plugins.py        # 插件注册与发现
│       ├── core/             # 核心 orchestration
│       ├── io/               # 数据读写（CSV/JSON/YAML）
│       └── viz/              # 可视化后端（Matplotlib, Plotly, Console, Streamlit）
├── tests/                    # 测试目录（test_*.py）
├── configs/                  # 示例配置文件
├── examples/                 # 可运行示例脚本
├── docs/                     # 架构文档 & API 参考
├── pyproject.toml            # 项目配置（依赖、ruff、mypy、pytest）
├── .pre-commit-config.yaml   # Pre-commit 钩子配置
└── README.md                 # 项目总览 README
```

---

**再次感谢您的贡献！** 🎉 如有疑问，欢迎在 [Issues](https://github.com/qhWangAntoneva/experiment-engine/issues) 中提问。
