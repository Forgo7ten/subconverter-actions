# subconverter-actions

利用GithubActions将自己的订阅通过[subconverter](https://github.com/tindy2013/subconverter)转换工具转换，并上传至特定的gist。

这里采用的是[asdlokj1qpi23/subconverter](https://github.com/asdlokj1qpi23/subconverter)的fork版本，其支持Hysteria2协议。

## 使用步骤

1.  Fork 本仓库

2.  在你自己 Fork 的仓库进行设置`Settings - Actions - General - Allow all actions and reusable workflows`，别忘了`save`

3.  然后`Settings - Secrets - Actions - New repository secret`，按下面例子新建几个`secrets`：

    | secrets Name     | Value                                                        |
    | ---------------- | ------------------------------------------------------------ |
    | `PERSONAL_TOKEN` | Github Personal Access Token（[在此创建](https://github.com/settings/tokens/new?scopes=gist&description=subconverter-action)） |
    | `GIST_ID`        | 要更新的Gist ID（**注意Secret**）                            |
    | `CONVERT_PARAM`  | 配置参数                                                     |

    1.   `PERSONAL_TOKEN`：个人访问令牌，没啥好说的。

    2.   `GIST_ID`：**需要自己新建**一个gist，填入id。`https://gist.github.com/{UserName}/{GistId}`

    3.   `CONVERT_PARAM`：这个比较复杂，是下述json格式的base64编码。`key`是上传至gist的文件名，`value`值是通过在线订阅转换前端生成的后端参数。

        ```json
        {"sub1.yml": "?target=clash&insert=false&exclude=%E5%A5%97%E9%A4%90%E5%88%B0%E6%9C%9F%7C%E8%8A%82%E7%82%B9%E8%B6%85%E6%97%B6%7C%E6%9B%B4%E6%8D%A2%7C%E5%89%A9%E4%BD%99%E6%B5%81%E9%87%8F%7C%E5%88%B0%E6%9C%9F%E6%97%B6%E9%97%B4%7CTG%E7%BE%A4%7C%E5%AE%98%E7%BD%91&interval=259200&emoji=true&list=true&xudp=false&udp=true&tfo=false&expand=true&scv=true&fdn=false&new_name=true&url=SUBURL", "sub2.yml": "?target=clash&insert=false&exclude=%E5%A5%97%E9%A4%90%E5%88%B0%E6%9C%9F%7C%E8%8A%82%E7%82%B9%E8%B6%85%E6%97%B6%7C%E6%9B%B4%E6%8D%A2%7C%E5%89%A9%E4%BD%99%E6%B5%81%E9%87%8F%7C%E5%88%B0%E6%9C%9F%E6%97%B6%E9%97%B4%7CTG%E7%BE%A4%7C%E5%AE%98%E7%BD%91&interval=259200&emoji=true&list=true&xudp=false&udp=true&tfo=false&expand=true&scv=true&fdn=false&new_name=true&url=SUBURL"}
        ```

        在线转换生成的订阅链接，sub之后的参数即为value（**包含?号**），也可以尝试使用`update.py`中的`test_param()`来生成。



如果Actions没自动运行，自己随便改点啥push一下触发。



在线订阅转换前端有：

-   [Subscription Converter (sub-web.netlify.app)](https://sub-web.netlify.app/)
-   [在线订阅转换工具 (v1.mk)](https://suburl.v1.mk/)
-   [品云订阅转换 (id9.cc)](https://id9.cc/)

不介意隐私可以直接用上述在线订阅转换的后端。



如果切换subconverter版本为官方版（目前还不支持Hysteria2 until 20240116），需要更改`UpdateGist.yml`中的docker，或注释掉docker用下载的subconverter文件，注意架构。

## 其他

推荐个[便宜大碗的t](https://pp.hnekoo.top/#/register?code=i8x7SbRK)，包年15r、或不限时1TB25r，还日常打8折，用Hysteria2协议速度杠杠的。
