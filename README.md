# Mihomo 配置与 Subconverter 模板

`mihomo-native.yaml` 是公开的配置模板。它不含生效的 `proxy-providers`，只保留注释示例。需要订阅时，使用 `mihomo.py providers` 生成一份包含 Provider 的独立配置；不要把带真实订阅 URL 的输出公开分享。

`converter-base.yaml`、`standard/subconverter-standard.ini` 和 `extended/subconverter-extended.ini` 由原生模板生成。`lib/` 存放实现代码，日常只运行根目录的 `mihomo.py`。

## 环境与命令

需要 Python 和 PyYAML。以下示例用 `uv` 临时提供 PyYAML；若当前 Python 已安装 PyYAML，可以直接运行 `python3 mihomo.py ...`。

| 命令 | 用途 |
| --- | --- |
| `providers` | 从 Mihomo YAML 提取 Provider 名称和 URL，或交互输入，生成完整配置 |
| `build` | 从原生模板生成共享配置和两份 Subconverter INI |
| `check` | 只检查生成文件是否与原生模板同步 |
| `verify` | 离线检查配置结构、策略组引用和转换后处理 |
| `convert` | 请求自建 Subconverter，随后整理其输出 |
| `finalize` | 整理已经下载的转换器原始 YAML，不发起转换请求 |

```bash
uv run --no-project --with pyyaml python3 mihomo.py --help
uv run --no-project --with pyyaml python3 mihomo.py verify
```

## 添加订阅 Provider

从已有配置提取 `proxy-providers` 下每个条目的**名称和 URL**：

```bash
uv run --no-project --with pyyaml python3 mihomo.py providers \
  --sourcefile '/绝对路径/现有配置.yaml' \
  --output './mihomo-with-providers.yaml'
```

不传 `--sourcefile` 时进入交互模式，每次输入一行名称、下一行 URL；在名称提示处直接回车结束：

```bash
uv run --no-project --with pyyaml python3 mihomo.py providers \
  --output './mihomo-with-providers.yaml'
```

例如依次输入 `00_personal`、它的订阅 URL、`10_hneko`、它的订阅 URL，最后输入空行。导入时保留原名称和顺序，只读取名称与 URL；名称可使用字母、数字、点、下划线和连字符。其它 Provider 字段统一使用注释示例的模板：HTTP 类型、`86400` 秒更新、`100` 秒健康检查、相同的 `exclude-filter`，缓存路径按名称生成。

输出保留原生模板的其余配置，权限为 `0600`，且不会覆盖已有文件。源文件不会被修改；其控制器密钥也不会复制到输出，输出沿用原生模板中的密钥。输入 URL 不会打印到命令输出。

## 构建与检查转换器模板

修改 `mihomo-native.yaml` 后运行：

```bash
uv run --no-project --with pyyaml python3 mihomo.py build
uv run --no-project --with pyyaml python3 mihomo.py check
uv run --no-project --with pyyaml python3 mihomo.py verify
```

`check` 和 `verify` 都不会写文件。原生模板有 24 个策略组：16 个 `select` 在前，8 个 `url-test` 在后。地区手动组定义筛选正则，对应自动组通过 YAML 引用复用。`converter-base.yaml` 保存 DNS、TUN、规则等共享内容，转换后由脚本恢复完整策略组及其顺序。

## 使用 Subconverter

将共享配置和对应 INI 安装到**自建**转换器。标准版示例：

```bash
cp converter-base.yaml '/path/to/subconverter/base/converter-base.yaml'
cp standard/subconverter-standard.ini '/path/to/subconverter/base/config/subconverter-standard.ini'
```

增强版将第二条命令的源文件换成 `extended/subconverter-extended.ini`，目标换成自建 SubConverter-Extended 的 `base/config/subconverter-extended.ini`；共享配置同样放在其 `base/converter-base.yaml`。

启动转换器后，使用含订阅 Provider 的配置作为 `--source`：

```bash
uv run --no-project --with pyyaml python3 mihomo.py convert \
  --backend standard \
  --source './mihomo-with-providers.yaml' \
  --endpoint 'http://127.0.0.1:25500' \
  --output './mihomo-standard.yaml'
```

增强版改用 `--backend extended`。标准版输出静态节点，订阅变化后需要重新转换；增强版保留远程 Provider，并应用相同的 Provider 模板。两种输出都会恢复原生模板的策略组、筛选条件和顺序。转换器会收到真实订阅 URL，请使用可信的自建服务。

如果已经下载了转换器原始 YAML，可跳过 HTTP 请求：

```bash
uv run --no-project --with pyyaml python3 mihomo.py finalize \
  --backend standard \
  --input './converted.yaml' \
  --source './mihomo-with-providers.yaml' \
  --output './mihomo-standard.yaml'
```

`convert` 和 `finalize` 不会覆盖已有输出文件。使用 `mihomo.py <命令> --help` 查看参数。离线检查不能代替目标设备上的 Mihomo 核心和真实转换器测试。

## 其他

推荐个[便宜大碗的t](https://goflybit.com/register?code=GHqArOrM)。
