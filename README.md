# 非洲研究图谱 v2 | China–Africa Research Atlas

> 一套可在本地或静态网站运行的 54 国交互式研究图谱：**14 个研究维度**、世界银行指标、UN Comtrade 贸易更新程序、已核验项目与政策线索、来源链接、国别比较及本地笔记。
>
> **当前完成程度**：功能模块与数据接口已经实现；世界银行数据支持浏览器在线查询和 GitHub Actions 快照；UN Comtrade 贸易提供周期更新脚本，部署执行后才显示返回的可用数据；投资、债务、民调等专题数据文件已创建但大部分尚未导入。网页**不虚构未取得的数据**。

## 1. 怎样启动

- **最容易**：双击 `非洲研究图谱_v2_可直接打开.html` 单文件版。地图、6 条核验资料、资料源、笔记在本地可用。世界银行指标需要浏览器联网访问原始 API。
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

个人笔记使用浏览器的 `localStorage`，不能在不同设备自动同步。网站公开发布后，网页本身是公开访问的，不适合存储私人或敏感研究资料；需要私密账号时应独立加入认证及私有数据库。

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
