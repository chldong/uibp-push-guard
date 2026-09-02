# uibp-push-guard

一个用于 UIBP 编程智能体的会话信息与 Docker 推送守护技能。

## 功能

- **新会话开始检查**：第一条用户提示必须包含 `项目名称`、`项目作者`、`项目描述`，缺失时只追问缺失项。
- **自动生成英文项目名**：根据项目信息自动生成 `project_name_en`，并创建同名目录存放项目所有文件。
- **推送前检查**：用户要求推送 Docker 镜像到 UIBP 底座时，必须包含 `本体用户名`、`本体密码`；推送路径和英文项目名称默认自动生成，并与项目目录名保持一致。
- **Docker 登录**：推送前先执行 `docker login reg.saitron.net`。
- **Docker annotations**：构建镜像时将 `project_name`、`project_author`、`project_description`、`project_name_en` 写入 OCI annotation，便于通过 Harbor API 顶层 `annotations` 字段查看项目信息。
- **本体密码保存询问**：登录成功后询问用户是否保存本体密码，只有用户明确同意才写入状态文件。
- **版本号强制 +0.1**：每次推送前版本号固定增加 `0.1`，初始版本为 `0.0`，第一次推送为 `0.1`，并作为 Docker TAG。
- **状态持久化**：项目信息、推送信息和版本号保存在英文项目名称目录内的 `.push-guard-state.json`，即 `<项目根目录>/<英文项目名称>/.push-guard-state.json`。
- **本体密码脱敏**：查看状态时 `body_password` 显示为 `******`。

## 构建与推送规则

```bash
# 登录 UIBP 底座镜像仓库
docker login reg.saitron.net -u <本体用户名> --password-stdin

# 构建镜像并写入项目信息 annotations（合并成一行）
# 注意：这里使用 OCI annotation（--annotation），不要使用 --label，Harbor API 顶层 annotations 才能展示项目信息
# 注意：加 --provenance=false --sbom=false，避免生成 OCI index + attestation 导致 Harbor API 顶层 artifact 读不到 annotation
docker build --push --provenance=false --sbom=false --annotation "project_name=<项目名称>" --annotation "project_author=<项目作者>" --annotation "project_description=<项目描述>" --annotation "project_name_en=<英文项目名称>" -t reg.saitron.net/<本体用户名>/<英文项目名称>:<TAG> <项目根目录>/<英文项目名称>
# 使用 --push 后无需再单独执行 docker push
```

其中 `<TAG>` 为每次推送前强制 `+0.1` 后的版本号，例如 `0.1`。

## 目录结构

```
uibp-push-guard/
├── SKILL.md
├── README.md
└── scripts/
    └── guard.py
```

## 安装

将整个 `uibp-push-guard` 目录放到你的技能目录中。不同环境的技能目录可能不同，常见位置：

- UIBP 技能目录：`<项目根目录>/.pi/skills/uibp-push-guard/` 或 agent 配置的技能目录

也可以先在当前目录直接测试脚本。

## 脚本用法

```bash
# 初始化状态文件
python3 scripts/guard.py init --state my-app/.push-guard-state.json

# 写入项目信息
python3 scripts/guard.py set --key project_name --value "示例项目" --state my-app/.push-guard-state.json
python3 scripts/guard.py set --key project_author --value "张三" --state my-app/.push-guard-state.json
python3 scripts/guard.py set --key project_description --value "示例描述" --state my-app/.push-guard-state.json
python3 scripts/guard.py set --key project_name_en --value "my-app" --state my-app/.push-guard-state.json

# 查看会话场景缺失字段
python3 scripts/guard.py missing --scope session --state my-app/.push-guard-state.json

# 查看推送场景缺失字段
python3 scripts/guard.py missing --scope push --state my-app/.push-guard-state.json

# 版本号 +0.1
python3 scripts/guard.py bump-version --state my-app/.push-guard-state.json

# 查看完整状态（本体密码脱敏）
python3 scripts/guard.py show --state my-app/.push-guard-state.json
```

## 环境变量

推送要素支持从环境变量读取，优先级最高：

- `BODY_USERNAME`
- `BODY_PASSWORD`
- `PUSH_PATH`（可选，覆盖默认自动生成的 `reg.saitron.net/<本体用户名>/英文项目名称`）

> 英文项目名称 `project_name_en` 默认以新会话开始时自动生成并创建目录的名称为准，不推荐用环境变量覆盖，以保证推送镜像名与项目目录名一致。
