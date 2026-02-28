# Win11 任务计划程序配置（每天自动跑）

## 1) 先准备 Python 环境
```bash
python -m venv .venv
.venv\\Scripts\\pip install pyyaml playwright
.venv\\Scripts\\python -m playwright install chromium
```

## 2) 本地手工验证
```bash
.venv\\Scripts\\python automation/main.py --config automation/config/sites.example.yaml --run-date 2025-02-17
```

## 3) 创建 `run_download.bat`
```bat
@echo off
cd /d D:\path\to\my-revenue
call .venv\Scripts\activate.bat
python automation\main.py --config automation\config\sites.example.yaml
```

## 4) 设置任务计划程序
1. 打开“任务计划程序” -> 创建任务。
2. 常规：
   - 名称：`daily-data-download`
   - 勾选“不管用户是否登录都要运行”（按公司策略）
3. 触发器：
   - 每周一到周五，建议 08:30。
4. 操作：
   - 程序/脚本：`D:\path\to\my-revenue\run_download.bat`
5. 条件：按需取消“仅在交流电源时运行”。
6. 设置：勾选“如果任务失败，按以下间隔重新启动”。

## 5) 结果检查
- 下载目录：`downloads/YYMMDD`
- 日志：`logs/YYYY-MM-DD.log`
- 汇总：`logs/result_YYYYMMDD.csv`
