---
name: uibp-push-guard
description: >
  在每次新会话开始时检查用户第一条提示词是否包含项目名称、项目作者、项目描述，缺失则主动提问补齐；
  在用户要求推送 Docker 镜像到 UIBP 底座时检查本体用户名、本体密码、推送路径、英文项目名称是否齐全，缺失则主动提问补齐；
  每次推送前强制将版本号增加 0.1 并作为 Docker TAG；推送成功后询问用户是否保存本体密码。
allowed-tools: Bash, Read, Write, Edit
---

# 项目信息与推送守护技能

本技能用于保证每个会话开始和每次推送前都满足强制的信息完整性要求。

## 状态文件

- 默认状态文件路径：`{{project_root_dir}}/<project_name_en>/.push-guard-state.json`


- 状态文件结构：

      ```json
      {
      "project_name": "",
      "project_author": "",
      "project_description": "",
      "project_name_en": "",
      "body_username": "",
      "body_password": "",
      "push_path": "",
      "version": "0.0"
      }
      ```

- 辅助脚本路径：`{{current_skill_dir_path}}/scripts/guard.py`


- `project_name_en`：英文项目名称，用于 Docker 镜像名。
- `push_path`：完整 Docker 仓库路径（不含 TAG），例如 `reg.saitron.net/uibp_user/my-app`。
- `version`：初始 `0.0`，每次推送前 `+0.1` 并作为 Docker TAG。

---

## 一、新会话开始检查

在收到本会话**第一条用户消息**时：

1. 提取三个字段：`项目名称`、`项目作者`、`项目描述`。
2. 若全部存在且明确则继续；否则只询问缺失字段：
   ```
   开始前请先补充以下项目信息：
   1. 项目名称
   2. 项目作者
   3. 项目描述
   ```
   补齐前不执行开发、修改、推送等其他任务。

3. 自动生成英文项目名称 `project_name_en`：
   - 用户已给出则优先使用；否则根据项目名称、描述自动生成（拼音、英文翻译或简洁短语）。
   - 规范化：只保留小写字母、数字、`-`、`_`、`.`；空格转 `-`；不以分隔符开头或结尾。
   - 告知用户，例如：`已自动创建英文项目名称：demo-project`。

4. 创建项目目录：
   ```bash
   mkdir -p {{project_root_dir}}/<project_name_en>
   ```
   此后本项目所有文件（代码、配置、文档、状态文件等）都创建在该目录下；目录已存在则复用，不覆盖。

5. 写入状态文件：
   ```bash
   python {{current_skill_dir_path}}/scripts/guard.py init --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   python {{current_skill_dir_path}}/scripts/guard.py set --key project_name --value "项目名称" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   python {{current_skill_dir_path}}/scripts/guard.py set --key project_author --value "项目作者" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   python {{current_skill_dir_path}}/scripts/guard.py set --key project_description --value "项目描述" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   python {{current_skill_dir_path}}/scripts/guard.py set --key project_name_en --value "生成的英文项目名称" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   ```

6. 完成后继续执行用户请求，把项目文件写入 `{{project_root_dir}}/{{project_name_en}}/` 下。

---

## 二、Dockerfile 镜像源规范（国内环境）

编写 Dockerfile 时优先使用国内镜像源，保证构建成功率与速度：

1. **基础镜像（`FROM`）**：首次编译镜像时优先使用 `docker.m.daocloud.io` 前缀，例如：
   ```
   FROM docker.m.daocloud.io/library/python:3.11-slim
   FROM docker.m.daocloud.io/library/node:20-alpine
   ```

2. **包管理器镜像源**（pip、apt、npm、yum 等）同样切换到国内镜像：
   - pip：清华 `https://pypi.tuna.tsinghua.edu.cn/simple/` 或阿里云 `https://mirrors.aliyun.com/pypi/simple/`
   - apt：阿里云 `http://mirrors.aliyun.com/` 或清华 `https://mirrors.tuna.tsinghua.edu.cn/`
   - npm：阿里云 `https://registry.npmmirror.com`

3. **适用边界**：默认国内环境编译使用上述加速源；海外环境或用户明确要求时可保留默认源。

---

## 三、Docker 推送前检查

推送目标为 **UIBP 底座**：`reg.saitron.net/<本体用户名>/<英文项目名称>[:TAG]`。

当用户消息包含明确推送意图时（如 `推送`、`push`、`上传推送`、`发布推送`、`推到...`），按以下步骤执行：

### 1. 确认推送要素

- `本体用户名`：用于 `docker login`。
- `本体密码`：用于 `docker login`。
- `英文项目名称` `project_name_en`：优先从状态文件读取；缺失则先补齐并自动生成。
- `推送路径`：默认自动生成 `reg.saitron.net/<body_username>/<project_name_en>`；用户消息或环境变量 `PUSH_PATH` 提供完整路径时优先使用，但其最后一段必须与 `project_name_en` 一致，不一致时以 `project_name_en` 为准。

字段来源优先级：环境变量（`BODY_USERNAME`、`BODY_PASSWORD`、`PUSH_PATH`）> 当前用户消息 > 状态文件 > 自动生成。

### 2. 缺失则提问

`本体用户名` 或 `本体密码` 缺失时只询问缺失字段：
```
推送前请先补充以下信息：
1. 本体用户名
2. 本体密码
```
补齐前不得执行 `docker login` 或 `docker push`。

### 3. 写入自动生成的推送路径

状态文件中 `push_path` 为空时：
```bash
python {{current_skill_dir_path}}/scripts/guard.py set --key push_path --value "reg.saitron.net/实际本体用户名/生成的英文项目名称" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
```

### 4. 执行 Docker 登录

```bash
printf '%s\n' "$BODY_PASSWORD" | docker login reg.saitron.net -u "$BODY_USERNAME" --password-stdin
```
环境变量不可用时，临时使用用户提供的用户名和密码执行等价命令。登录成功后再推送。

### 5. 询问是否保存本体密码

登录成功后询问：`是否将本体密码保存到状态文件？`
- 用户明确同意后才写入状态文件：
  ```bash
  python {{current_skill_dir_path}}/scripts/guard.py set --key body_password --value "用户提供的本体密码" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
  ```
- 否则只在当前会话使用，不落盘；优先建议使用环境变量 `BODY_PASSWORD`。

---

## 四、构建镜像 + 版本号 +0.1（强制）

每次推送前必须递增版本号并构建镜像：

1. 确保状态文件存在：
   ```bash
   python {{current_skill_dir_path}}/scripts/guard.py init --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   ```

2. 递增版本号（脚本输出新版本号，如 `0.1`）：
   ```bash
   python {{current_skill_dir_path}}/scripts/guard.py bump-version --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
   ```

3. 构建前环境检查：确认 `docker buildx` 可用并存在兼容 builder。
   ```bash
   docker buildx version || { echo "错误：docker buildx 未安装，请参考 https://docs.docker.com/buildx/working-with-buildx/ 安装"; exit 1; }
   docker buildx create --name multiarch --use 2>/dev/null || true
   ```
   `docker buildx version` 失败则停止推送并告知安装 buildx。

4. 构建并直接推送，把 `project_name`、`project_author`、`project_description`、`project_name_en` 写入 OCI annotation：
   ```bash
   docker buildx build --builder multiarch --push --provenance=false --sbom=false --output type=registry,oci-mediatypes=true --annotation "project_name=<项目名称>" --annotation "project_author=<项目作者>" --annotation "project_description=<项目描述>" --annotation "project_name_en=<英文项目名称>" -t reg.saitron.net/<body_username>/<英文项目名称>:<新版本号> {{project_root_dir}}/<英文项目名称>
   ```
   关键参数：
   - `--builder multiarch`：使用支持 OCI 的 buildkit builder（v0.31+），避免默认 driver 不输出 OCI manifest。
   - `--output type=registry,oci-mediatypes=true`：强制输出 OCI manifest，annotations 才能出现在顶层。
   - `--provenance=false --sbom=false`：防止生成 OCI index 包裹层，确保 annotations 落在 Harbor 可读取的顶层。
   - `--annotation`（不要用 `--label`）：`--label` 只写入镜像 config 内部，Harbor 属性总览无法读取。

   已构建过且代码未变化可跳过重复构建，但需确认镜像已带上述 annotations。

5. `--push` 直接完成推送，无需单独 `docker push`；目标示例 `reg.saitron.net/uibp_user/my-app:0.1`。

6. 推送说明中明确包含新版本号；步长固定 `0.1`，TAG 不加 `v` 前缀。

---

## 五、辅助脚本命令

```bash
# 初始化状态文件（已存在则补全默认字段）
python {{current_skill_dir_path}}/scripts/guard.py init --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json

# 写入字段
python {{current_skill_dir_path}}/scripts/guard.py set --key project_name --value "示例项目" --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json

# 读取字段
python {{current_skill_dir_path}}/scripts/guard.py get --key version --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json

# 检查缺失字段
python {{current_skill_dir_path}}/scripts/guard.py missing --scope session --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
python {{current_skill_dir_path}}/scripts/guard.py missing --scope push --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json

# 查看完整状态（本体密码脱敏）
python {{current_skill_dir_path}}/scripts/guard.py show --state {{project_root_dir}}/<project_name_en>/.push-guard-state.json
```
