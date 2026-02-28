# my-revenue 自动下载脚手架

这是一套面向“多网站、账号密码登录、按工作日规则下载 Excel”的自动化骨架，适用于 Win11。

## 已包含能力
- 周一下载上周五~周日，其他工作日下载前一天。
- 支持站点差异流程（直接下载 / 查询后下载 / 查询后进入文件再下载）。
- 支持“某些站点周一必须按天下载”，其余可按区间下载。
- 统一输出目录：`downloads/YYMMDD`。
- 统一日志输出：运行日志 + 结果汇总 CSV。

## 快速开始
1. 安装依赖：
   ```bash
   pip install pyyaml playwright
   playwright install chromium
   ```
2. 复制并填写配置：`automation/config/sites.example.yaml`。
3. 运行：
   ```bash
   python automation/main.py --config automation/config/sites.example.yaml
   ```

> 说明：当前 `run_site_download()` 是占位函数，用于接入各网站 Playwright 具体步骤。

## 目录结构
- `automation/main.py`：主控脚本
- `automation/config/sites.example.yaml`：站点配置示例
- `automation/templates/需求确认表.md`：需求收集模板
- `automation/docs/Win11任务计划配置.md`：Win11 定时运行说明
