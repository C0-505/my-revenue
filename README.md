# my-revenue 自动下载脚手架

这是一套面向“多网站、账号密码登录、按工作日规则下载 Excel”的自动化骨架，适用于 Win11。

## 这版已按你给的首站点信息预置
- 站点：`https://semplus.kisvan.co.kr/`
- 用户名固定：`0050000001`
- 密码从环境变量读取：`SEMPLUS_PASSWORD`
- 门店自动循环：`01` 到 `09`
- 周一按天下载（上周五、周六、周日）
- 查询后弹出新页面，再在新页面点击 Excel 下载（`#btn_Excel`）

## 你问的：run 具体怎么操作？
下面按 **第一次运行**、**日常运行**、**定时运行** 三种情况写。

### A) 第一次运行（建议先 dry-run）
1. 打开 PowerShell，进入项目目录。
2. 创建虚拟环境并安装依赖：
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install pyyaml playwright
   .\.venv\Scripts\python -m playwright install chromium
   ```
3. 先跑不访问网站的演练（dry-run）：
   ```powershell
   .\.venv\Scripts\python -m automation.main --config automation/config/sites.test.json --dry-run
   ```
4. 看到成功后，再跑真实站点（可视化调试）：
   ```powershell
   $env:SEMPLUS_PASSWORD = "你的真实密码"
   .\.venv\Scripts\python -m automation.main --config automation/config/sites.example.yaml --headful
   ```

### B) 日常手工运行
- 无界面运行（更接近定时任务）：
  ```powershell
  $env:SEMPLUS_PASSWORD = "你的真实密码"
  .\.venv\Scripts\python -m automation.main --config automation/config/sites.example.yaml
  ```

### C) 双击 bat 脚本运行（最省事）
仓库已提供 3 个脚本：
- `automation/scripts/run_dry_run.bat`：本地演练
- `automation/scripts/run_real_headful.bat`：真实站点 + 可视化
- `automation/scripts/run_real_headless.bat`：真实站点 + 无界面

> 注意：真实运行前要先设置 `SEMPLUS_PASSWORD` 环境变量。

### D) 一键放到桌面（你这次要的）
在 PowerShell 里执行：
```powershell
powershell -ExecutionPolicy Bypass -File .\automation\scripts\install_desktop_launcher.ps1
```
执行后桌面会生成：
- `数据自动下载-演练.bat`（先跑 dry-run）
- `数据自动下载-正式.bat`（真实下载）

也可以双击：`automation/scripts/install_desktop_launcher.bat` 来创建桌面启动程序。

## 结果看哪里
- 下载目录：`downloads/YYMMDD`
- 日志：`logs/YYYY-MM-DD.log`
- 汇总：`logs/result_YYYYMMDD.csv`

## 流程类型说明
- `direct_download`：填条件后直接下载。
- `query_then_download`：先点“查询/검색”，再点下载。
- `query_open_file_then_download`：先查询，再点结果文件，再下载。

你这个站点是：**`query_then_download` + `query_opens_popup: true`**。

## 目录结构
- `automation/main.py`：主控脚本
- `automation/sites.py`：单站点 Playwright 执行器（含“查询后弹窗”处理）
- `automation/config/sites.example.yaml`：首站点配置示例
- `automation/config/sites.test.json`：可离线执行的测试配置
- `automation/scripts/*.bat`：Win11 直接运行脚本
- `tests/test_rules.py`：日期与任务拆分测试
