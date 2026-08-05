import fs from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = "/Volumes/WD_BLACK/汾酒尼泊尔";
const OUT = path.join(ROOT, "outputs", "20260713_fenjiu_nepal");
const QA = path.join(ROOT, "qa", "xlsx");
await fs.mkdir(OUT, { recursive: true });
await fs.mkdir(QA, { recursive: true });

const readJson = async (name) => JSON.parse(await fs.readFile(path.join(ROOT, name), "utf8"));
const root = await readJson("research_root.json");
const channels = await readJson("research_channels.json");
const culture = await readJson("research_culture_compliance.json");
const execution = await readJson("research_execution.json");

const stringy = (v) => {
  if (v === null || v === undefined) return null;
  if (Array.isArray(v)) return v.map(stringy).filter((x) => x !== null).join(" | ");
  if (typeof v === "object") return Object.entries(v).map(([k, val]) => `${k}:${stringy(val)}`).join(" | ");
  return v;
};
const shown = (v, fallback = "待验证") => (v === null || v === undefined || v === "" ? fallback : v);
const num = (v) => typeof v === "number" ? v : (v === null || v === undefined || v === "" ? null : Number(v));
const colLetter = (n) => {
  let s = "";
  while (n > 0) { n--; s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26); }
  return s;
};
const BLUE = "#1F4E79";
const BLUE2 = "#D9EAF7";
const GOLD = "#FFF2CC";
const RED = "#FCE4D6";
const GREEN = "#E2F0D9";
const GRAY = "#F2F4F7";
const WHITE = "#FFFFFF";

function styleTitle(sheet, range, title, subtitle = "") {
  const c1 = range.split(":")[0];
  const c2 = range.split(":")[1];
  sheet.mergeCells(range);
  sheet.getRange(c1).values = [[title]];
  sheet.getRange(range).format = { fill: BLUE, font: { bold: true, color: WHITE, size: 16 }, verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 30;
  if (subtitle) {
    const endCol = c2.replace(/\d+/g, "");
    sheet.mergeCells(`A2:${endCol}2`);
    sheet.getRange("A2").values = [[subtitle]];
    sheet.getRange(`A2:${endCol}2`).format = { fill: BLUE2, font: { color: "#334155", italic: true, size: 9 }, wrapText: true };
    sheet.getRange(`A2:${endCol}2`).format.rowHeight = 30;
  }
}

function writeTableSheet(wb, cfg) {
  const { name, title, subtitle, headers, rows, widths, tableName, validations = [], numberFormats = {}, conditional = [] } = cfg;
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  const lastCol = colLetter(headers.length);
  styleTitle(sheet, `A1:${lastCol}1`, title, subtitle);
  const matrix = [headers, ...rows];
  sheet.getRange(`A3:${lastCol}${rows.length + 3}`).values = matrix;
  sheet.getRange(`A3:${lastCol}3`).format = {
    fill: BLUE,
    font: { bold: true, color: WHITE, size: 9 },
    wrapText: true,
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#B8C2CC" },
  };
  sheet.getRange(`A4:${lastCol}${rows.length + 3}`).format = {
    font: { color: "#1F2937", size: 9 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#E2E8F0" },
  };
  if (rows.length > 0) {
    const table = sheet.tables.add(`A3:${lastCol}${rows.length + 3}`, true, tableName);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
  }
  sheet.freezePanes.freezeRows(3);
  widths.forEach((w, i) => { sheet.getRange(`${colLetter(i + 1)}:${colLetter(i + 1)}`).format.columnWidth = w; });
  sheet.getRange("1:1").format.rowHeight = 30;
  sheet.getRange("2:2").format.rowHeight = 30;
  sheet.getRange("3:3").format.rowHeight = 36;
  for (const [col, fmt] of Object.entries(numberFormats)) sheet.getRange(`${col}4:${col}${rows.length + 3}`).format.numberFormat = fmt;
  for (const v of validations) sheet.getRange(`${v.col}4:${v.col}${Math.max(rows.length + 3, v.toRow || rows.length + 3)}`).dataValidation = { rule: { type: "list", values: v.values } };
  for (const c of conditional) sheet.getRange(c.range).conditionalFormats.add(c.type, c.config);
  return sheet;
}

async function exportAndVerify(wb, filename, previewSheets) {
  const info = await wb.inspect({ kind: "sheet", include: "id,name", maxChars: 5000 });
  console.log(`${filename} sheets`, info.ndjson);
  const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: `${filename} error scan` });
  console.log(`${filename} errors`, errors.ndjson);
  for (const spec of previewSheets) {
    const sheetName = typeof spec === "string" ? spec : spec.sheet;
    const label = typeof spec === "string" ? spec : (spec.label || `${sheetName}_${spec.range.replace(/:/g, "-")}`);
    const renderOptions = { sheetName, scale: 1, format: "png" };
    if (typeof spec === "string") renderOptions.autoCrop = "all";
    else renderOptions.range = spec.range;
    const preview = await wb.render(renderOptions);
    await fs.writeFile(path.join(QA, `${filename.replace(/\.xlsx$/, "")}_${label}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  const blob = await SpreadsheetFile.exportXlsx(wb);
  await blob.save(path.join(OUT, filename));
}

const leads = channels.leads || [];
const leadHeaders = ["lead_id","企业名称","英文名称","当地名称","城市","区域","完整地址","Google Maps搜索路由","客户类型","主要业务","进口烈酒","中高端客户","官网","Facebook","Instagram","LinkedIn","TikTok","公开电话","公开邮箱","WhatsApp/Viber","决策人","职位","公开联系方式","来源ID","证据URL","来源更新时间","最近验证","公开证据状态","推荐接触方式","推荐语言","产品切入口","线索评分","等级","优先级","交叉验证","当前状态","下一步","风险备注","评分理由"];
const leadRows = leads.map((x) => [
  x.lead_id, x.enterprise_name, x.english_name, shown(x.local_name), x.city, shown(x.area), shown(x.full_address), x.google_maps_url,
  x.customer_type, x.main_business, x.imported_spirits_status, x.upper_midmarket_status, shown(x.website, "未找到公开官网"), shown(x.facebook, "未找到公开信息"), shown(x.instagram, "未找到公开信息"),
  shown(x.linkedin, "未找到公开信息"), shown(x.tiktok, "未找到公开信息"), shown(x.public_phone, "未找到公开电话"), shown(x.public_email, "未找到公开邮箱"), shown(x.whatsapp_or_viber, "待人工确认"), shown(x.decision_maker_name, "待找负责人"), shown(x.decision_maker_title, "待找负责人"),
  shown(x.decision_maker_public_contact, "待找负责人"), stringy(x.source_ids), stringy(x.evidence_urls), stringy(x.source_updated) || "日期未标", shown(x.last_verified_date, "待人工验证"),
  x.evidence_status, x.recommended_contact_method, x.recommended_language, x.recommended_product_entry, x.lead_score?.score ?? null,
  x.lead_score?.grade ?? null, x.priority, x.cross_source_status, x.current_status, x.next_action, x.risk_note, x.lead_score?.reason,
]);
const leadWb = Workbook.create();
writeTableSheet(leadWb, {
  name: "Leads", title: "渠道商及终端线索数据库", subtitle: `截至2026-07-13：${leads.length}条唯一公开线索；目录发现不等于正在营业或可成交。`,
  headers: leadHeaders, rows: leadRows, widths: [12,22,20,18,15,16,24,28,15,18,12,12,24,24,22,22,20,15,22,16,16,14,18,18,35,18,12,14,24,14,30,10,8,10,24,12,34,30,40], tableName: "LeadsTable",
  validations: [{ col: "AJ", values: ["待验证","已验证","待找负责人","可首次接触","已接触","有回复","待预约","已预约","待品鉴","试销谈判","已上架","观察动销","已补货","暂缓","淘汰","禁止继续联系"] }],
  numberFormats: { AF: "0", AA: "yyyy-mm-dd" },
  conditional: [
    { range: `AF4:AF${leadRows.length+3}`, type: "colorScale", config: { colors: ["#FEE2E2","#FEF3C7","#DCFCE7"], thresholds: ["min","50%","max"] } },
    { range: `AJ4:AJ${leadRows.length+3}`, type: "containsText", config: { text: "禁止", format: { fill: "#FECACA", font: { color: "#991B1B", bold: true } } } },
  ],
});
const high = leads.filter((x) => x.priority === "high");
writeTableSheet(leadWb, {
  name: "HighPriority", title: "高优先级独立域名双源线索", subtitle: "至少2个证据URL、2个独立来源域名且评分较高；仍需人工核验营业、资质和负责人。",
  headers: ["lead_id","企业","城市","区域","类型","评分","公开证据状态","证据URL","接触方式","下一步"],
  rows: high.map((x) => [x.lead_id,x.enterprise_name,x.city,x.area,x.customer_type,x.lead_score?.score,x.evidence_status,stringy(x.evidence_urls),x.recommended_contact_method,x.next_action]),
  widths: [12,22,14,16,16,9,14,42,24,34], tableName: "HighPriorityTable", numberFormats: { F: "0" },
});
writeTableSheet(leadWb, {
  name: "DataRules", title: "字段、状态与验证规则", subtitle: "人工不重复做AI已经完成的整理；只处理身份、法律、语言和现实动作。",
  headers: ["规则","执行标准","禁止"], rows: [
    ["入库最小条件","企业名称+城市+类别+至少1个公开URL","无来源企业"],
    ["高优先级","至少2个证据URL+2个独立域名+评分+下一步","用单一目录或同域页面当双源"],
    ["决策人","只记录公开业务身份/联系方式","推测私人号码"],
    ["去重","标准名称+电话+域名+地址","同企业多门店不注明分店"],
    ["时效","每次接触前复查；超过90天重新验证","把访问日期当来源发布日期"],
    ["状态","只按真实动作升级","目录存在→已接触/已验证"],
  ], widths: [18,42,30], tableName: "DataRulesTable",
});
await exportAndVerify(leadWb, "10_渠道商及终端线索数据库.xlsx", [
  {sheet:"Leads",range:"A1:J30",label:"Leads_A-J"},
  {sheet:"Leads",range:"K1:T30",label:"Leads_K-T"},
  {sheet:"Leads",range:"U1:AL30",label:"Leads_U-AL"},
  {sheet:"HighPriority",range:"A1:J27",label:"HighPriority"},
  "DataRules",
]);

const scoringWb = Workbook.create();
const cityRows = (channels.city_scoring || []).map((x) => [x.city, ...(Object.values(x.score_components || {})), x.total, x.confidence, x.status, x.priority, x.entry_condition, x.caution, stringy(x.raw_evidence)]);
writeTableSheet(scoringWb, {
  name: "城市评分", title: "城市评分｜100分", subtitle: "公开证据代理的决策模型，不是城市级酒类销售统计。",
  headers: ["城市","消费15","HORECA15","进口酒15","商务旅游10","渠道10","中亚餐饮10","数字10","差异10","执行5","总分","置信度","状态","优先级","进入条件","提醒","原始证据"],
  rows: cityRows, widths: [18,8,8,8,8,8,8,8,8,8,9,10,10,8,34,30,42], tableName: "CityScoreTable", numberFormats: { B:"0",C:"0",D:"0",E:"0",F:"0",G:"0",H:"0",I:"0",J:"0",K:"0" },
  conditional: [{ range:`K4:K${cityRows.length+3}`, type:"colorScale", config:{ colors:["#FEE2E2","#FEF3C7","#DCFCE7"], thresholds:["min","50%","max"] } }],
});
function scoreSheet(name, title, dims, tableName, seedRows, subtitle) {
  const headers = ["对象","证据状态",...dims.map((d)=>`${d.name}(${d.weight})`),"总分","等级","评分理由","下一步"];
  const rows = seedRows.length ? seedRows : [["BLOCKED：暂无合规对象","BLOCKED",...dims.map(()=>0),null,null,"未获得书面合规许可，不录入对象。","合规解除后再评分"]];
  const sheet = writeTableSheet(scoringWb,{name,title,subtitle,headers,rows,widths:[24,14,...dims.map(()=>9),10,9,40,34],tableName,validations:[{col:"B",values:["KNOWN","INFERRED","COMPUTED","NEEDS_VERIFY","BLOCKED"]}]});
  const scoreCol = 3 + dims.length;
  const gradeCol = scoreCol + 1;
  for(let r=4;r<rows.length+4;r++){
    sheet.getRange(`${colLetter(scoreCol)}${r}`).formulas=[[`=SUM(C${r}:${colLetter(scoreCol-1)}${r})`]];
    sheet.getRange(`${colLetter(gradeCol)}${r}`).formulas=[[`=IF(${colLetter(scoreCol)}${r}>=80,"S",IF(${colLetter(scoreCol)}${r}>=65,"A",IF(${colLetter(scoreCol)}${r}>=50,"B",IF(${colLetter(scoreCol)}${r}>=35,"C","D"))))`]];
  }
  sheet.getRange(`${colLetter(scoreCol)}4:${colLetter(scoreCol)}${rows.length+3}`).format.numberFormat="0";
  dims.forEach((d, i) => {
    sheet.getRange(`${colLetter(i+3)}4:${colLetter(i+3)}${rows.length+3}`).dataValidation = { rule: { type: "whole", operator: "between", formula1: 0, formula2: d.weight } };
  });
}
const models = execution.scoring_models || {};
const dimsFrom = (model, fallback) => {
  if (Array.isArray(model)) return model.map((x)=>({name:x.dimension||x.name,weight:x.weight}));
  if (model && model.weights) return Object.entries(model.weights).map(([name,weight])=>({name,weight}));
  return fallback;
};
const dealerDims = dimsFrom(models.dealer_or_wholesaler || models.distributor || models.dealer, [
  {name:"客群匹配",weight:15},{name:"渠道覆盖",weight:15},{name:"销售执行",weight:15},{name:"试销意愿",weight:15},{name:"可触达",weight:10},{name:"信誉回款",weight:10},{name:"动销",weight:10},{name:"数据",weight:5},{name:"价格纪律",weight:5}
]);
const outletDims = dimsFrom(models.outlet || models.hotel_restaurant_bar_store || models.terminal, [
  {name:"客群",weight:20},{name:"场景",weight:15},{name:"进口酒经验",weight:15},{name:"动销",weight:15},{name:"可触达",weight:10},{name:"试销",weight:10},{name:"形象",weight:5},{name:"位置",weight:5},{name:"数据",weight:5}
]);
const creatorDims = dimsFrom(models.creator || models.tiktok_creator, [
  {name:"成年受众",weight:20},{name:"本地可信",weight:15},{name:"相关性",weight:15},{name:"互动质量",weight:15},{name:"城市覆盖",weight:10},{name:"品牌安全",weight:10},{name:"制作",weight:10},{name:"成本",weight:5}
]);
const contactability = (x, max=10) => Math.min(max, (x.public_phone ? 4 : 0) + (x.public_email ? 3 : 0) + (x.website ? 3 : 0));
const dealerSeed = high.filter((x)=>["liquor_retail","ecommerce","instant_delivery"].includes(x.customer_type)).map((x)=>[
  x.enterprise_name,"INFERRED",
  12, x.customer_type === "ecommerce" ? 10 : 8, 0, 0, contactability(x,10), 0, 0, 0, 0,
  null,null,
  "仅按公开客群匹配、渠道可见度和可触达性预评分；销售团队、意愿、回款、动销、数据与价格纪律均待访谈。",
  x.next_action,
]);
const outletSeed = high.filter((x)=>["hotel","resort","banquet","restaurant_bar"].includes(x.customer_type)).map((x)=>[
  x.enterprise_name,"INFERRED",
  x.customer_type === "restaurant_bar" ? 15 : 17, 12, 9, 0, contactability(x,10), 0, 4, 4, 0,
  null,null,
  "仅按公开客群、场景、进口酒可能性、形象与位置预评分；真实动销、试销意愿和数据能力待人工确认。",
  x.next_action,
]);
scoreSheet("经销商评分","经销商及批发商评分｜100分",dealerDims,"DealerScoreTable",dealerSeed,"当前未发现可公开核实的独立经销商/批发商对象；此处仅列高优先零售/电商渠道候选的保守预评分。");
scoreSheet("终端评分","酒店/餐厅/酒吧/门店评分｜100分",outletDims,"OutletScoreTable",outletSeed,"高优先终端的公开证据预评分；未知能力按0分，须由访谈和试销改写。");
scoreSheet("创作者评分","TikTok创作者评分｜仅在合规解除后使用",creatorDims,"CreatorScoreTable",[],"当前方案C，公开酒类推广BLOCKED；仅保留100分模型，不制造创作者候选。");
await exportAndVerify(scoringWb,"11_城市_渠道商_终端_创作者评分表.xlsx",[
  {sheet:"城市评分",range:"A1:Q7",label:"城市评分"},
  {sheet:"经销商评分",range:"A1:H15",label:"经销商评分_A-H"},
  {sheet:"经销商评分",range:"I1:N15",label:"经销商评分_I-N"},
  {sheet:"终端评分",range:"A1:H15",label:"终端评分_A-H"},
  {sheet:"终端评分",range:"I1:N15",label:"终端评分_I-N"},
  {sheet:"创作者评分",range:"A1:H15",label:"创作者评分_A-H"},
  {sheet:"创作者评分",range:"I1:N15",label:"创作者评分_I-N"},
]);

const crmWb = Workbook.create();
const crmHeaders=["lead_id","企业","城市","类型","优先级","评分","状态","首次接触","最近接触","下一动作日期","下一动作","负责人","回复分类","预约","品鉴","试销","上架","补货","拒绝原因","风险"];
const crmSeed=[...high,...leads.filter((x)=>x.priority!=="high").sort((a,b)=>(b.lead_score?.score||0)-(a.lead_score?.score||0)).slice(0,Math.max(0,50-high.length))];
const crmRows=crmSeed.map((x)=>[x.lead_id,x.enterprise_name,x.city,x.customer_type,x.priority,x.lead_score?.score,x.current_status,null,null,null,x.next_action,"","","否","否","否","否","否","",x.risk_note]);
writeTableSheet(crmWb,{name:"CRM",title:"90天CRM执行表",subtitle:"首批50条工作队列；只把真实动作写回状态。",headers:crmHeaders,rows:crmRows,widths:[12,22,15,16,10,9,14,12,12,12,34,12,16,8,8,8,8,8,24,30],tableName:"CRMTable",validations:[{col:"G",values:["待验证","已验证","待找负责人","可首次接触","已接触","有回复","待预约","已预约","待品鉴","试销谈判","已上架","观察动销","已补货","暂缓","淘汰","禁止继续联系"]},{col:"N",values:["是","否"]},{col:"O",values:["是","否"]},{col:"P",values:["是","否"]},{col:"Q",values:["是","否"]},{col:"R",values:["是","否"]}],numberFormats:{F:"0",H:"yyyy-mm-dd",I:"yyyy-mm-dd",J:"yyyy-mm-dd"}});
const dash=crmWb.worksheets.add("Dashboard"); dash.showGridLines=false; styleTitle(dash,"A1:F1","90天CRM看板","所有KPI来自CRM表；空白=尚未发生，不写成0业绩通过。");
dash.getRange("A3:C12").values=[["KPI","当前","90天目标"],["原始线索",leads.length,"300+"],["已验证",null,"150+"],["高优先",high.length,"50+"],["实际接触",null,"50-80"],["有效回复",null,"15-30"],["预约/品鉴",null,"5-12"],["试销",null,"8-15"],["已补货",null,"试销的>=30%"],["合规事件",0,0]];
dash.getRange("B5").formulas=[[`=COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"已验证")`]];
dash.getRange("B7").formulas=[[`=COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"已接触")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"有回复")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"待预约")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"已预约")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"待品鉴")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"试销谈判")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"已上架")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"观察动销")+COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},"已补货")`]];
dash.getRange("B8").formulas=[[`=SUM(COUNTIF('CRM'!$G$4:$G$${crmRows.length+3},{"有回复","待预约","已预约","待品鉴","试销谈判","已上架","观察动销","已补货"}))`]];
dash.getRange("B9").formulas=[[`=COUNTIF('CRM'!$O$4:$O$${crmRows.length+3},"是")+COUNTIFS('CRM'!$N$4:$N$${crmRows.length+3},"是",'CRM'!$O$4:$O$${crmRows.length+3},"<>是")`]];
dash.getRange("B10").formulas=[[`=COUNTIF('CRM'!$P$4:$P$${crmRows.length+3},"是")`]];
dash.getRange("B11").formulas=[[`=COUNTIF('CRM'!$R$4:$R$${crmRows.length+3},"是")`]];
dash.getRange("A3:C3").format={fill:BLUE,font:{bold:true,color:WHITE},borders:{preset:"all",style:"thin",color:"#B8C2CC"}};
dash.getRange("A4:C12").format={font:{size:10},borders:{preset:"inside",style:"thin",color:"#E2E8F0"}};
dash.getRange("A:A").format.columnWidth=24; dash.getRange("B:C").format.columnWidth=18; dash.freezePanes.freezeRows(3);
await exportAndVerify(crmWb,"12_90天CRM执行看板.xlsx",["Dashboard",{sheet:"CRM",range:"A1:J25",label:"CRM_A-J"},{sheet:"CRM",range:"K1:T25",label:"CRM_K-T"}]);

const contentWb=Workbook.create();
const topics=execution.short_video_topics||[];
writeTableSheet(contentWb,{name:"30选题",title:"30个短视频选题",subtitle:"脚本池不等于发布许可；当前Plan C，公开发布BLOCKED。",headers:["id","选题","支柱","前三秒","销售场景","风险"],rows:topics.map((x)=>[x.id,x.title,x.pillar,x.hook,x.sales_scene,x.risk]),widths:[8,28,14,30,20,36],tableName:"TopicsTable"});
const scripts=execution.shoot_ready_scripts||[];
writeTableSheet(contentWb,{name:"12脚本",title:"12条可直接拍摄脚本",subtitle:"Nepali均为NEEDS_VERIFY草稿；演员25+，实际发布须书面合规。",headers:["id","标题","时长秒","前三秒","演员","场景","道具","镜头表","英文字幕","Nepali草稿","发布文案","Nepali文案草稿","关键词","风险","指标","销售场景"],rows:scripts.map((x)=>[x.id,x.title,x.duration_seconds,x.hook_first_3s,stringy(x.actors),x.scene,stringy(x.props),stringy(x.shots),stringy(x.subtitle_en),stringy(x.subtitle_ne_draft),x.caption_en,x.caption_ne_draft,stringy(x.search_keywords),stringy(x.risk_check),stringy(x.target_metrics),x.sales_scene]),widths:[8,26,9,30,18,22,18,45,38,38,34,34,22,38,30,22],tableName:"ScriptsTable",numberFormats:{C:"0"}});
const calendar=execution.content_calendar?.weeks||execution.content_calendar||[];
writeTableSheet(contentWb,{name:"12周日历",title:"12周内容与销售联动日历",subtitle:"内容节奏服务销售验证；若合规未解除则仅做内部素材/培训。",headers:["周","主题","内容","销售联动","合规闸门","指标"],rows:calendar.map((x)=>{
  const content = Array.isArray(x.publish) && x.publish.length > 0 ? x.publish : (x.items||x.content||x.actions);
  const salesLink = x.sales_link||x.sales_action||x.test||"发布前准备；不做公开销售CTA";
  const metric = x.metrics||x.kpi||x.test||"准备项完成率；阻断项清零率";
  return [x.week,x.theme||x.focus||x.status,stringy(content),salesLink,x.compliance_gate||x.gate||execution.content_calendar?.publishing_gate,stringy(metric)];
}),widths:[9,20,38,28,30,24],tableName:"ContentCalendarTable"});
const metrics=execution.content_metric_definitions||[];
writeTableSheet(contentWb,{name:"指标口径",title:"内容指标口径",subtitle:"不同平台口径不得混算；销售反馈优先于播放量。",headers:["指标","定义/公式","来源/平台","注意"],rows:(Array.isArray(metrics)?metrics:Object.values(metrics)).map((x)=>[x.metric||x.name,x.definition||x.formula,x.platform||x.source,x.warning||x.caution||x.note]),widths:[20,40,24,36],tableName:"MetricsTable"});
await exportAndVerify(contentWb,"13_短视频内容日历与脚本库.xlsx",[
  {sheet:"30选题",range:"A1:F20",label:"30选题"},
  {sheet:"12脚本",range:"A1:H15",label:"12脚本_A-H"},
  {sheet:"12脚本",range:"I1:P15",label:"12脚本_I-P"},
  "12周日历","指标口径",
]);

const riskWb=Workbook.create(); const risks=execution.risk_matrix||[];
writeTableSheet(riskWb,{name:"风险矩阵",title:"困难、风险、解决方案矩阵",subtitle:"风险不是附录：出现平台/监管警告、虚假身份、投诉时立即进入人工和BLOCKED。",headers:["id","困难","概率","影响","早期信号","AI处理","人工介入条件","解决方案","失败备用方案"],rows:risks.map((x)=>[x.id,x.risk,x.probability,x.impact,x.early_signal,x.ai,x.human_trigger,x.solution,x.fallback]),widths:[8,30,10,10,28,28,28,34,30],tableName:"RiskTable",validations:[{col:"C",values:["低","中","高"]},{col:"D",values:["低","中","高"]}],conditional:[{range:`D4:D${risks.length+3}`,type:"containsText",config:{text:"高",format:{fill:"#FECACA",font:{color:"#991B1B",bold:true}}}}]});
await exportAndVerify(riskWb,"14_困难_风险_解决方案矩阵.xlsx",[{sheet:"风险矩阵",range:"A1:I20",label:"风险矩阵"}]);

const queueWb=Workbook.create();
const queueRows=[
  ["当地酒类广告/内容书面意见","PHSA s45及平台功能","高","法规和问题清单","请律师/主管机关逐项书面回答","A/B/C条件方案","当前保持方案C","7天","继续BLOCKED","","否"],
  ["国代商业数据","SKU/价格/利润/库存缺失","高","已列21项清单","补齐并签字","先核心SKU或一次性全量","一次性补齐全量","3天","无法报价/评分","","否"],
  ["平台入驻","费用/抽佣/年龄/许可不公开","高","已列平台和联系人","向平台索取书面入驻包","分平台询问或联合询问","先Cheers/Barmandoo/Drinks Nepal/Daraz","7天","B2C延后","","否"],
  ["Nepali母语审核","公开文本不能由机器定稿","高","已有NEEDS_VERIFY草稿","母语者+合规负责人逐条审","先外联或先品鉴文本","先审首批外联与品鉴","发布/发送前","继续BLOCKED","","否"],
  ["Top20首次外联","真实发送/身份核验","中",`383线索、Top${high.length}独立域名双源`,"对Top20逐条发送并写回","电话/Email/Messenger","按D1/D3/D7/D14节奏","2天","无法校准渠道","","是"],
  ["封闭品鉴","口感/配餐必须真实测试","中","已有量杯/盲评方案","约2-3个持牌场所","纯饮/加水/加冰小杯组","先5/10/15ml+水+食物","14天","无产品适配证据","","是"],
  ["Claude复核","本机Claude CLI不可用","低","已生成Word任务包","外部Claude按P0-P3复核","延后或外部执行","主体研究继续，复核保持BLOCKED","交付后","少一层反方复核","","是"],
];
writeTableSheet(queueWb,{name:"人工队列",title:"人工介入队列",subtitle:"人工只做法律、商业输入、语言和现实动作；完成后重新交回AI。",headers:["事项","触发原因","风险","AI已完成","人工只做什么","可选方案","建议方案","最晚处理节点","不处理影响","处理结果","是否重新交给AI"],rows:queueRows,widths:[24,30,10,30,32,24,30,16,28,28,14],tableName:"HumanQueueTable",validations:[{col:"C",values:["低","中","高"]},{col:"K",values:["是","否"]}],conditional:[{range:`C4:C${queueRows.length+3}`,type:"containsText",config:{text:"高",format:{fill:"#FECACA",font:{color:"#991B1B",bold:true}}}}]});
await exportAndVerify(queueWb,"15_人工介入队列.xlsx",[{sheet:"人工队列",range:"A1:K11",label:"人工队列"}]);

const allSources=[];
for(const arr of [root.sources,channels.sources,culture.evidence_registry,execution.evidence_sources]) for(const s of (arr||[])) allSources.push(s);
const sourceByUrl=new Map(); const sourceAliasMap={}; const sources=[];
for(const original of allSources){
  const key=original.url||original.id;
  if(!key) continue;
  let canonical=sourceByUrl.get(key);
  if(!canonical){
    canonical={...original,alias_ids:[]};
    sourceByUrl.set(key,canonical); sources.push(canonical);
  }
  if(original.id && !canonical.alias_ids.includes(original.id)) canonical.alias_ids.push(original.id);
  if(original.id) sourceAliasMap[original.id]=canonical.id;
}
const normalizedLeads=leads.map((x)=>({
  ...x,
  public_evidence_status:x.evidence_status,
  business_verified:String(x.current_status||"").toLowerCase()==="已验证" || String(x.current_status||"").toLowerCase()==="verified",
  source_id_aliases:x.source_ids,
  source_ids:(x.source_ids||[]).map((id)=>sourceAliasMap[id]||id),
}));
const normalizedGrade=(s)=>{const raw=String(s.grade||s.level||""); return raw.includes("/")?"B":(raw||"C");};
const defaultConfidence=(grade)=>grade==="A"?"high":grade==="B"?"medium-high":grade==="C"?"medium":"low";
const normalizedSources=sources.map((s)=>{
  const grade=normalizedGrade(s);
  return {
    id:s.id,
    alias_ids:s.alias_ids||[],
    title:s.title||"未命名来源",
    url:s.url,
    published_or_updated:s.published_or_updated||s.publication_or_update_date||s.published||"日期未标",
    accessed:s.accessed||s.access_date||"2026-07-13",
    source_type:s.source_type||s.type||"公开网页",
    grade,
    confidence:s.confidence||s.credibility||defaultConfidence(grade),
    label:s.label||s.conclusion_tag||"NEEDS_VERIFY",
    conclusion:s.conclusion||s.claim||s.use||"仅作线索，结论待补",
    limitations:s.limitations||s.note||"动态网页/目录，执行前复查；不证明合作意愿。",
  };
});
const sourceWb=Workbook.create();
writeTableSheet(sourceWb,{name:"来源索引",title:"来源与证据索引",subtitle:`按URL归并为${normalizedSources.length}条；alias_ids保留全部原始引用ID。访问日期2026-07-13。`,headers:["canonical_id","别名ID","标题","URL","发布/更新","访问日期","来源类型","等级","可信度","判断标签","对应结论","局限"],rows:normalizedSources.map((s)=>[s.id,stringy(s.alias_ids),s.title,s.url,s.published_or_updated,s.accessed,s.source_type,s.grade,s.confidence,s.label,s.conclusion,s.limitations]),widths:[14,24,36,48,14,12,20,8,12,14,44,36],tableName:"SourceIndexTable"});
await exportAndVerify(sourceWb,"16_来源与证据索引.xlsx",[
  {sheet:"来源索引",range:"A1:F25",label:"来源索引_A-F"},
  {sheet:"来源索引",range:"G1:L25",label:"来源索引_G-L"},
]);

const finalJson={
  metadata:{title:"汾酒尼泊尔机器可读取的渠道数据",generated_on:"2026-07-13",lead_count:leads.length,source_count:normalizedSources.length,truth_note:"Directory discovery is not operating-status or willingness-to-buy confirmation. Missing public information is null."},
  status_legend:{KNOWN:"已确认事实",INFERRED:"基于证据推论",COMPUTED:"经过计算",NEEDS_VERIFY:"需要当地确认",BLOCKED:"暂时阻断"},
  city_scoring:channels.city_scoring,
  ecommerce_and_delivery_status:channels.ecommerce_and_delivery_status,
  competitor_snapshot:channels.competitor_snapshot,
  leads:normalizedLeads,
  sources:normalizedSources,
};
await fs.writeFile(path.join(OUT,"17_机器可读取的渠道数据.json"),JSON.stringify(finalJson,null,2),"utf8");
for(const filename of ["10_渠道商及终端线索数据库.xlsx","11_城市_渠道商_终端_创作者评分表.xlsx","12_90天CRM执行看板.xlsx","13_短视频内容日历与脚本库.xlsx","14_困难_风险_解决方案矩阵.xlsx","15_人工介入队列.xlsx","16_来源与证据索引.xlsx"]){
  execFileSync("/Users/fan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3",[path.join(ROOT,"patch_xlsx_freeze.py"),path.join(OUT,filename),"3"]);
}
console.log(`Built 7 XLSX files and JSON in ${OUT}`);
