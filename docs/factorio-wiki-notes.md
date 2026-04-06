# Factorio Wiki / API 复查笔记

## 本次用到的资料

### Display panel 的蓝图字段

来源：

- [LuaSurface / BlueprintEntity](https://lua-api.factorio.com/latest/classes/LuaSurface.html)

记录：

- `display-panel` 蓝图实体支持 `text`、`icon`、`always_show`、`show_in_chart`、`control_behavior`
- `always_show` 可用于让显示内容长期显示，不必只靠手动开关细节模式
- `control_behavior.messages` 可按条件显示图标和文字，适合给显示器做稳定的说明标签
- 这次蓝图里把输入端和输出端都改成了 `display-panel`

### 常量组合器里的虚拟信号编码

来源：

- [Blueprint string format](https://wiki.factorio.com/Blueprint_string_format)
- [Constant combinator](https://wiki.factorio.com/Constant_combinator)

记录：

- `constant-combinator` 的 `sections.sections[].filters[]` 如果写的是虚拟信号，不能只写 `name`
- 例如 `signal-info` 这类信号，过滤项里要显式带上 `type: "virtual"`
- 否则导入时会被当成物品名解析，出现 `Unknown item name: signal-info`
- 这类问题尤其容易出现在给显示器提供常亮说明信号的辅助常量组合器上

### 显示器说明的恒真条件

来源：

- 实测

记录：

- `display-panel` 的 `control_behavior.messages[].condition` 可以用 `signal-1 = signal-1` 作为恒真条件
- 这种写法不依赖额外常量组合器，也不会受接入电路网络里是否有信号影响
- 当前蓝图已改成这种写法，并删掉了原先只为显示器说明服务的辅助常量组合器

### 蓝图实体里的 display-panel 类型

来源：

- [Display panel](https://wiki.factorio.com/Display_panel)

记录：

- 显示器适合做静态说明、图标提示和状态展示
- 这次主要拿它替代原先的电线杆端点，用来明确标出“库存输入”和“输出信号”

### 回差 / 锁存思路

来源：

- [Tutorial:Circuit network cookbook](https://wiki.factorio.com/Tutorial:Circuit_network_cookbook)

记录：

- 官方示例明确提到 latch 用来引入 hysteresis，避免设备在阈值附近快速来回切换
- 对这次蓝图，更适合用“低阈值启动 + 高阈值释放”而不是单纯延时防抖
- 这个思路尤其适合库存补货和平台资源平衡
- 如果锁存实现不稳，优先改成“候选值 + 保持优先级”的结构，减少多级相互抢占

### Alt-mode 相关说明

来源：

- [Tutorial:Circuit network cookbook](https://wiki.factorio.com/Tutorial:Circuit_network_cookbook)

记录：

- 官方教程里提到组合器和电路设置的显示依赖 Alt-mode 相关选项
- 这次改成显示器后，优先依赖 `always_show` 而不是只依赖 Alt-mode

## 这份笔记的用途

- 以后改蓝图时先查这里，确认某个实体在蓝图 JSON 里有哪些字段
- 如果后续又查了 wiki / API，继续往这份文件里追加即可
