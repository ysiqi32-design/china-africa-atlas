# 非洲研究图谱 v4（新闻动态与本地上传版） | China–Africa Research Atlas

> 一套可在本地或静态网站运行的 54 国交互式研究图谱：**14 个研究维度**、世界银行指标、UN Comtrade 贸易更新程序、已核验项目与政策线索、来源链接、国别比较及本地笔记。
>
> **当前完成程度**：功能模块与数据接口已经实现；世界银行数据支持浏览器在线查询和 GitHub Actions 快照；UN Comtrade 贸易提供周期更新脚本，部署执行后才显示返回的可用数据；投资、债务、民调等专题数据文件已创建但大部分尚未导入。网页**不虚构未取得的数据**。


## V4：国别最新动态每日自动发现（待核验）

### 数据来源和频率

- 新闻主索引改用 [AllAfrica 官方 RSS](https://allafrica.com/misc/tools/rss.html)：按 AllAfrica 的国别分类读取英文和法文 RSS，筛选标题或摘要中提及 China/Chinese/Chine/chinois 的条目。AllAfrica 官方说明其内容来自90多个非洲新闻机构及自有记者，并允许网站展示标题，但要求注明并链接 AllAfrica 或所用 feed 页面。
- `.github/workflows/update-news.yml` 每天 05:43 UTC（北京时间13:43）最多轮换4国；英、法 RSS 均尝试读取，约14天完成一轮。每国保留最近90天内最多45条线索。GitHub Actions 运行可能延误或失败，RSS 分类覆盖也会因国家和来源而异。
- GDELT 在 GitHub Actions 上连续触发 429 后不再作为主采集源；其旧版采集脚本保留作诊断用途。新闻数据写入失败国家状态后再生成 bundle 和提交，写文件采用原子替换，单国失败不覆盖已保存线索。
- 前端显示标题、RSS日期、来源域名、文章链接、所属国家和机器粗分类。只保存元数据，不存全文；所有自动入库新闻均为「待核验线索」。RSS 日期由来源提供，不保证等于实际事件发生时间。
- 「资料类型」筛选可查媒体线索；政府和研究机构官方来源仍在14个研究维度下供交叉核查。点击「加入核验清单」或「忽略此线索」的决定保存在当前浏览器；新闻面板可导出待核验清单 CSV。
- 新闻发现不会自动变成已核验政策事件。核验时应打开原始文章，查阅政府及企业一手材料，确认报道日期、各方说法，再手动提交记录。

首次运行后查看 `data/news.json` 的 `checked_at_utc`、`country_status` 和 `errors`。各国状态单独记录最近检查时间、最近成功时间和来源错误；每次部分成功都会保留成功国家的数据。GitHub Pages 发布后点击新闻区「↻ 读取最新快照」可刷新页面快照。

本地离线测试：

```bash
python -m unittest discover -s tests -p 'test_update_news_rss.py'
```

## 0. 新增：手动上传与完整本地备份（A方案）

网站右上角点击 **「＋ 手动上传 / 我的资料」**，进入数据管理中心：

1. 在「国家」和「维度」中选择资料归属（若 CSV / XLSX / JSON 某行自带 `country` 与 `module`，则优先使用该行字段）。
2. 批量上传 **CSV、TSV、XLSX（Excel 第一个工作表）、JSON**；选择「统计」或「项目/事件」，点击「预览数据」，核对有效条数和错误行，再点击「确认保存」。
3. 也可以手动输入一条统计数据或研究事件，或上传 **PDF、DOCX、DOC、TXT、Markdown** 原始文档附件。暂不自动读取文献全文或提取引用；文件仍可以从相应国别档案下载。
4. 点击地图上的对应国家和维度，查看 **我的本地研究资料**（有明确「本地导入 / 待核验」标志），与网站现有官方数据分层展示、不相互覆盖。
5. **定期点击「导出完整备份」**，得到 `AfricaAtlas_本地研究资料完整备份_日期.json`，包含本地上传的记录、附件及原先的浏览器研究笔记；换电脑或清除浏览器缓存后可用「恢复备份」导入。可选择合并（相同 ID 覆盖）或清空再恢复。系统不自动发送到 GitHub。

推荐 **使用 Chrome / Edge，在固定域名的 GitHub Pages 网站上上传**。网站的 IndexedDB 存储按「浏览器配置文件＋网站来源」隔离：相同资料无法自动从 Chrome 同步到 Edge，换域名或通过另一个本地文件路径访问时也可能互不相通；浏览器隐私模式、站点数据清理、磁盘配额或设备故障可能导致丢失。**请把备份 JSON 文件另存至你自己的可靠位置。**

### 导入格式示例（不要当成已核验真实数据）

统计 CSV（国家代码建议 ISO3，数值不能空，年份为整数）：
```csv
country,module,title,year,value,unit,source_name,source_url,status,summary
GIN,resources,铝土矿统计示例,2024,129.5,万吨,示例报告,https://example.org,待核验,仅演示字段
```
事件 CSV：
```csv
country,module,title,date,summary,source_name,source_url,status
SEN,diplomacy,外交政策文件示例,2025-01-01,仅演示字段,示例报告,https://example.org,待核验
```

`module` 接受如 `resources`, `trade`, `financing`, `opinion`, `projects` 等网站内部模块 ID，或对应维度标题。导入前请使用网站提供的模板，确认列名、货币单位、统计年份及统计口径；个人上传资料 **不能直接覆盖** 官方来源统计。

**限制**：单个上传文件最多 15MB，一次最多 10,000 行，XLSX 只读取首张工作表，不支持受密码保护的工作簿；普通文献附件最多 15MB。批量文件优先使用 UTF-8 CSV，其他编码先转换为 UTF-8。JSON 备份可能因为附件而变大；恢复的备份文件最大 85MB。受浏览器可用存储配额限制，大批量或大型资料保存可能失败。此方案无用户账户、无云端同步，访问公共网址不意味着本地材料公开。

## 1. 怎样启动

- **最容易**：双击 `非洲研究图谱_V4_可直接打开.html` 单文件版。地图、已有核验资料、资料源和手动上传功能在本地可用；但 file:// 方式的浏览器数据存储可能因浏览器安全策略不可用，建议使用 GitHub Pages 或 localhost。世界银行指标需要浏览器联网访问原始 API。
- **完整项目**：项目根目录可运行 `python -m http.server 8000`，浏览器打开 `http://localhost:8000`。也可以将整个文件夹发布到 GitHub Pages、Cloudflare Pages 或 Netlify。
- 项目部署后，每周可用 GitHub Actions 检查数据更新。单文件离线版不会自动接收 Actions 生成的数据，下载更新后的单文件才能同步快照。

## 2. 数据分别来自哪里

| 项目 | 文件 | 自动化状态 |
|---|---|---|
| 世界银行16项国家统计 | `data/worldbank_snapshot.json` | `scripts/update_worldbank.py` 定时检查；国别点击在线查询 |
| 双边商品贸易（中国作为报告国） | `data/trade.json` | `scripts/update_trade.py` 使用 UN Comtrade，存在公共预览配额 |
| 政策和项目核验线索 | `data/records.json` | 6条来源核验示例；新增需要审核后导入 |
| 其余专题 | `data/investment.json`, `data/financing.json` 等 | 结构已建，仍需按各自许可导入真实数据 |
| 前端离线数据集合 | `data/bundle.js` | `scripts/build_bundle.py` 从已有 JSON 生成，不创造新统计数字 |

主要公开来源及使用限制：
- 世界银行 [Indicators API v2](https://datahelpdesk.worldbank.org/knowledgebase/articles/898581) 无需 API 密钥，统计年份不等于调用日期。
- [UN Comtrade API](https://uncomtrade.org/docs/un-comtrade-api/) 的无密钥 `preview` 接口有严格的记录和频次限制；增加 `UN_COMTRADE_KEY` secret 可访问订阅范围内的接口，仍应遵守使用政策。
- [SAIS-CARI](https://www.sais-cari.org/data)、[Boston University CLA](https://www.bu.edu/gdp/chinese-loans-to-africa-database-data-download/)、[AidData](https://china.aiddata.org/)、[Afrobarometer](https://www.afrobarometer.org/) 和 [SIPRI](https://www.sipri.org/databases/armstransfers) 的下载格式、授权和统计定义不同；尚未将其宣称为自动接入。

## 3. 启动更新程序

需 Python 3.10+：

```bash
python -m pip install -r requirements.txt
python scripts/update_worldbank.py
python scripts/update_trade.py --start 2023 --end 2025
python scripts/build_bundle.py
```

更新脚本在外部 API 不可用或返回错误数据时，不会生成伪造统计数字。网络完全不可用时，世界银行脚本会拒绝覆盖已有的合格快照；Comtrade 脚本在没有任何新有效数据时也不会改写现有文件。

- `update_trade.py` 中国报告国 `reporterCode=156`；`X` 表示中国对某非洲国家的出口，`M` 表示中国从其进口，两者按 **USD** 存储。中国的出口不自动等于非洲国家自己的进口口径。
- 如果开通 UN Comtrade API 访问凭证，把它配置为 GitHub 仓库 Actions Secret `UN_COMTRADE_KEY`。**不要**把密钥写入网页代码或 Git 提交。
- 脚本不会擅自计算“该国对中国的贸易依赖率”，因为这种比例必须另行保证该国商品进出口总额和中国报告额的可比性。

## 4. 怎样填入14个维度的数据

每个 JSON 文件采用国家 ISO3 代码组织，例如：

```json
{
  "schema_version": 2,
  "dataset": "investment",
  "updated_at_utc": null,
  "countries": {
    "GIN": [
      {
        "indicator": "chinese_fdi_stock",
        "label": "中国对几内亚直接投资存量",
        "value": null,
        "unit": "USD",
        "year": 2024,
        "status": "no_public_data",
        "source_name": "示例记录：尚未取数",
        "source_url": "https://www.mofcom.gov.cn/"
      }
    ]
  }
}
```

上例 `value:null` **仅解释字段格式**，不是已经发现的几内亚数据。先校验文件 JSON 格式，然后运行 `python scripts/build_bundle.py`，前端会自动按 ISO3 展示模块记录。如果无实值，页面显示未公布。

事件与政策记录建议使用 CSV 模板 `templates/curated_records_template.csv`，含 `id,country,modules,type,date,title,summary,verification,source_name,source_url`；多个模块用分号隔开：

```bash
python scripts/import_curated.py templates/curated_records_template.csv
python scripts/import_curated.py your_reviewed_records.csv --commit
python scripts/build_bundle.py
```

首次调用是干运行只验证格式；加 `--commit` 才写回 `data/records.json`。导入**前**确认来源支持事实，区分官方主张、记者报道和已生效政策；不能将带争议指控改写成已证实事实。

## 5. 重要的统计区别

- 贸易额 ≠ 直接投资存量，WDI 的总体 FDI 净流入不是“中国在该国的 FDI”。
- 贷款承诺 ≠ 实际拨款 ≠ 未偿债务余额。
- 工程承包金额 ≠ 项目股权或最终所有权。
- 某国家统计资料缺失 ≠ 双方不存在合作，更不等于零。
- `year` 为被统计的年份，`updated_at_utc` 是本站抓取数据的时间，`observed_at` 为事件记录核查时间，三者不同。
- 开放数据使用时仍需遵守原始提供方许可；不能将有访问限制的数据集未经授权重新发布。

## 6. 自动任务与隐私

`.github/workflows/update-data.yml` 每周读取 WDI 和 UN Comtrade 数据，重新生成 `data/bundle.js`。GitHub Actions 定时执行会受到平台排队/失败、API访问限制影响，因此更新属于**周期检查**，不是实时流式数据。

研究笔记与新闻核验清单使用浏览器的 `localStorage`，不能在不同设备自动同步。网站公开发布后，网页本身是公开访问的，不适合存储私人或敏感研究资料；需要私密账号时应独立加入认证及私有数据库。

## 7. 目录

```
app.js                            前端地图、指标、比较与专题记录
style.css                         网站样式
index.html                        54国地理数据与页面
scripts/update_worldbank.py       世界银行真实数据采集
scripts/update_trade.py           联合国双边贸易数据采集
scripts/build_bundle.py           打包前端静态数据
scripts/import_curated.py         核验后批量导入资料
scripts/setup_research_data.py    初始化规范的空数据库
scripts/build_singlefile.py       更新独立HTML文件
data/*.json                       具统计来源及状态的国别数据
.github/workflows/update-data.yml 定时检查
```

### 通用专题CSV导入（适用于投资、债务、工程、军贸、民调等）

`templates/statistics_template.csv` 包含 `country,indicator,label,year,value,unit,source_name,source_url,status`。正式统计数值需设置 `status=verified` 且填入来源链接，空白 `value` 不会变成 0。

```bash
python scripts/import_statistics.py investment my_reviewed_fdi.csv       # 检查，不写入
python scripts/import_statistics.py investment my_reviewed_fdi.csv --commit
python scripts/build_bundle.py
```

此程序可以用于 `investment/financing/engineering/resources/industry/payments/security/multilateral/society/surveys/external/diplomacy` 12 类专题资料。贸易优先使用 Comtrade 结构化接口；主权主义/条约/社会事件请使用 `import_curated.py`，不要把叙事性内容伪装成统计指标。网站按国家和模块从以上文件读取核验资料。

## 8. GitHub Pages 发布（本仓库）

此仓库默认网址：`https://ysiqi32-design.github.io/china-africa-atlas/`（**仅在 GitHub Pages 成功启用及部署后才有效**）。

1. 仓库页面依次进入 **Settings → Pages → Build and deployment**，将 **Source** 设为 **GitHub Actions**。
2. 进入 **Actions**，查看 **Publish Atlas to GitHub Pages**，必要时点击 **Run workflow** 手动发布。
3. 同一页检查 **Refresh source-traceable country data**，可以使用 **Run workflow** 触发首次统计抓取；GitHub Actions 在默认分支有权限的情况下才可以提交更新后的数据。
4. GitHub Actions 如因仓库设置限制提交，需要到 **Settings → Actions → General → Workflow permissions**，选择 **Read and write permissions** 并保存。
5. 如果你获得 UN Comtrade 订阅 API 密钥，进入 **Settings → Secrets and variables → Actions → New repository secret**，名称填写 `UN_COMTRADE_KEY`，填写密钥；无密钥会尝试公共预览数据但可能不完整，脚本不会冒充完整覆盖。

**重要隐私说明**：本仓库当前为公开仓库。不要提交研究私密笔记、访问令牌、个人信息等。浏览器的本地研究笔记保存在浏览器 Local Storage 中，不随项目上传。


## 新闻采集源调整（2026-10）

初次 GDELT 运行在第49国附近被 GitHub Actions 取消，未到保存步骤；之后的限流修复成功保存了检查状态，但新运行仍在首个国家收到 HTTP 429，故网站没有新闻记录。为避免把平台限流误判为前端问题，主采集已切换到 AllAfrica 的公开英、法文国别 RSS；每日只轮换少数国家，两个语言源至少有一个成功时就保存该国结果。每次任务先运行离线解析测试，随后以原子方式写入 JSON。某国源失败时保留该国旧记录，提交可用国家的进度并在工作流末尾报告失败状态。
