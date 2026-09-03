# uibp-push-guard

一个用于 UIBP 编程智能体的会话信息与 Docker 推送守护技能。

## 功能

- **新会话开始检查**：首条提示必须包含 `项目名称`、`项目作者`、`项目描述`，缺失时只追问缺失项。
- **自动生成英文项目名**：根据项目信息生成 `project_name_en`，并创建同名目录存放所有文件。
- **国内镜像源规范**：编写 Dockerfile 优先使用阿里云、华为云、清华镜像；首次编译镜像 `FROM` 优先使用 `docker.m.daocloud.io`。
- **推送前检查**：推送 Docker 镜像到 UIBP 底座时需包含 `本体用户名`、`本体密码`；推送路径和英文项目名自动生成，并与目录名一致。
- **Docker 登录**：推送前先 `docker login reg.saitron.net`。
- **Docker annotations**：构建时把 `project_name`、`project_author`、`project_description`、`project_name_en` 写入 OCI annotation，便于 Harbor API 顶层 `annotations` 查看。
- **版本号强制 +0.1**：每次推送前版本号固定 `+0.1`，首次推送为 `0.1`，并作为 Docker TAG。
- **状态持久化与安全**：项目/推送信息与版本号保存在 `<英文项目名>/.push-guard-state.json`；本体密码查看时脱敏，仅在用户同意后保存。
