![视频脚本：每句旁白，都有该解释的画面](assets/readme/hero.png)

# 月明·视频脚本

把已确认选题与证据写成可制作的旁白和分镜，明确每段画面应该解释或证明什么。

## 你会得到什么

- 逐句旁白与镜次表
- 预估时长、字幕重点、素材需求和画面职责
- 明确的制作模式与下游交接材料

## 试着这样说

```text
用 moonlit-video-script。基于这份选题和实测材料写视频脚本。每段给出旁白、证据和画面职责，时长由内容决定。
```

## 安装与首次使用

将本仓库的完整目录交给支持本地 Skill 的 Agent 安装，保留 `SKILL.md` 与随附资源。已有同名版本时先检查差异；使用版本锁的工作区沿用自身升级机制。

让 Agent 安装：

```text
请安装这个 Skill：https://github.com/zzyong24/moonlit-video-script
```

也可通过 Skills CLI 安装：

```bash
npx skills add zzyong24/moonlit-video-script
```

## 配置与依赖

内容原则依赖 moonlit-business-copywriter；使用对标结构时接收 moonlit-benchmark-research 的来源。当前品牌规范和作品约定由使用方提供。脚本确认后按真人、HTML、数字人或 Excalidraw 模式交给对应 Skill。

## 数据与使用边界

文本由当前 Agent 处理，后续生成服务按制作模式使用。本 Skill 不将预估时长当作实际音频时间；数字人手势工具见 [组装工具](scripts/presenter-gestures/README.md)，人物视频与动作 catalog 由使用方提供。

## 配套 Skill

[benchmark-research](https://github.com/zzyong24/moonlit-benchmark-research) · [business-copywriter](https://github.com/zzyong24/moonlit-business-copywriter)

## 详细说明

执行流程与资源导航见 [SKILL.md](SKILL.md)。安装检查不代表真实业务验收；需要外部服务、账号登录或付费生成的步骤，应在使用者自己的环境中验证。

---

月明水清深 · `moonlit-video-script`

首图为 AI 生成的品牌概念插画，不是工具截图或执行结果。
